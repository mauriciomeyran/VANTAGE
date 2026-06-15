import json
import time
import uuid

from datetime import datetime

from flask import jsonify, request

from dashboard_notion import (
    query_blocked_vacancies,
    fetch_notion_page,
    write_patch_to_notion,
)

from dashboard_db import (
    get_db,
    append_event,
)

from dashboard_validation import run_python_validation

from layer_1_run import txt


# ── Helpers ───────────────────────────────────────────────────────────────────

def _new_instance_id():
    return 'inst_' + uuid.uuid4().hex[:8]


def _now():
    return datetime.utcnow().isoformat()


def _get_instance(conn, instance_id):
    return conn.execute(
        'SELECT * FROM instances WHERE instance_id = ?',
        (instance_id,)
    ).fetchone()


def _serialize_instance(row, conn):
    """Convierte una sqlite3.Row de instancia a dict JSON-serializable,
    incluyendo su audit log completo."""
    if row is None:
        return None

    payload  = json.loads(row['payload'])        if row['payload']        else {}
    proposed = json.loads(row['proposed_patch']) if row['proposed_patch'] else None

    events = conn.execute(
        '''
        SELECT sequence, event_type, payload, timestamp_unix
        FROM audit_events
        WHERE instance_id = ?
        ORDER BY sequence ASC
        ''',
        (row['instance_id'],)
    ).fetchall()

    audit_log = [
        {
            'sequence':   e['sequence'],
            'event_type': e['event_type'],
            'payload':    json.loads(e['payload']),
            'timestamp':  e['timestamp_unix'],
        }
        for e in events
    ]

    return {
        'instance_id':    row['instance_id'],
        'notion_page_id': row['notion_page_id'],
        'state':          row['state'],
        'version_id':     row['version_id'],
        'event_sequence': row['event_sequence'],
        'correlation_id': row['correlation_id'],
        'operator_id':    row['operator_id'],
        'payload':        payload,
        'proposed_patch': proposed,
        'block_reason':   row['block_reason'],
        'created_at':     row['created_at'],
        'updated_at':     row['updated_at'],
        'audit_log':      audit_log,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

def register_routes(app):

    # ── /health ───────────────────────────────────────────────────────────────
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'version': 'rt1-backend-1.0'})


    # ── /blocked-vacancies ────────────────────────────────────────────────────
    @app.route('/blocked-vacancies', methods=['GET'])
    def blocked_vacancies():
        try:
            response = query_blocked_vacancies()
        except Exception as e:
            return jsonify({'error': f'NOTION_QUERY_FAIL: {e}'}), 502

        with get_db() as conn:
            active_rows = conn.execute(
                '''
                SELECT notion_page_id FROM instances
                WHERE state NOT IN ('RETURNED_TO_CREATE', 'FAILED')
                '''
            ).fetchall()

        active_ids = {r['notion_page_id'] for r in active_rows}

        vacancies = []
        for page in response.get('results', []):
            page_id = page['id']
            props   = page['properties']
            vacancies.append({
                'notion_page_id': page_id,
                'marca':          txt(props.get('Marca')),
                'rol':            txt(props.get('Rol')),
                'url':            txt(props.get('URL')),
                'score':          props.get('Score', {}).get('number'),
                'vm_scope':       txt(props.get('VM_Scope')),
                'role_class':     txt(props.get('Role_Class')),
                'has_active_rt1': page_id in active_ids,
            })

        return jsonify({
            'vacancies':   vacancies,
            'count':       len(vacancies),
            'without_rt1': sum(1 for v in vacancies if not v['has_active_rt1']),
        })


    # ── POST /instances ───────────────────────────────────────────────────────
    @app.route('/instances', methods=['POST'])
    def create_instance():
        body           = request.get_json() or {}
        notion_page_id = body.get('notion_page_id', '').strip()

        if not notion_page_id:
            return jsonify({'error': 'MISSING_FIELD: notion_page_id'}), 400

        # Verificar que no exista instancia activa para esta vacante
        with get_db() as conn:
            existing = conn.execute(
                '''
                SELECT instance_id FROM instances
                WHERE notion_page_id = ?
                  AND state NOT IN ('RETURNED_TO_CREATE', 'FAILED')
                ''',
                (notion_page_id,)
            ).fetchone()

        if existing:
            return jsonify({
                'error': f'INSTANCE_ALREADY_ACTIVE: {existing["instance_id"]}'
            }), 409

        # Fetch payload desde Notion
        try:
            payload = fetch_notion_page(notion_page_id)
        except Exception as e:
            return jsonify({'error': f'NOTION_FETCH_FAIL: {e}'}), 502

        instance_id    = _new_instance_id()
        correlation_id = str(uuid.uuid4())
        now            = _now()

        with get_db() as conn:
            conn.execute(
                '''
                INSERT INTO instances (
                    instance_id, notion_page_id, state, version_id,
                    event_sequence, correlation_id, operator_id,
                    payload, proposed_patch, block_reason,
                    created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ''',
                (
                    instance_id, notion_page_id, 'BLOCKED', 1,
                    0, correlation_id, 'human',
                    json.dumps(payload), None, None,
                    now, now,
                )
            )

            append_event(
                conn,
                instance_id    = instance_id,
                sequence       = 1,
                correlation_id = correlation_id,
                causation_id   = None,
                event_type     = 'domain.instance.created',
                payload        = {'notion_page_id': notion_page_id, 'payload': payload},
            )

            conn.execute(
                'UPDATE instances SET event_sequence = 1 WHERE instance_id = ?',
                (instance_id,)
            )

            row = _get_instance(conn, instance_id)
            return jsonify(_serialize_instance(row, conn)), 201


    # ── GET /instances/<id> ───────────────────────────────────────────────────
    @app.route('/instances/<instance_id>', methods=['GET'])
    def get_instance(instance_id):
        with get_db() as conn:
            row = _get_instance(conn, instance_id)
            if row is None:
                return jsonify({'error': f'INSTANCE_NOT_FOUND: {instance_id}'}), 404
            return jsonify(_serialize_instance(row, conn))


    # ── POST /instances/<id>/patch ────────────────────────────────────────────
    @app.route('/instances/<instance_id>/patch', methods=['POST'])
    def propose_patch(instance_id):
        body  = request.get_json() or {}
        patch = body.get('patch', {})

        if not patch:
            return jsonify({'error': 'EMPTY_PATCH'}), 400

        with get_db() as conn:
            row = _get_instance(conn, instance_id)
            if row is None:
                return jsonify({'error': f'INSTANCE_NOT_FOUND: {instance_id}'}), 404

            if row['state'] != 'BLOCKED':
                return jsonify({
                    'error': f'INVALID_STATE: expected BLOCKED, got {row["state"]}'
                }), 409

            seq = row['event_sequence'] + 1
            now = _now()

            conn.execute(
                '''
                UPDATE instances
                SET proposed_patch  = ?,
                    event_sequence  = ?,
                    updated_at      = ?
                WHERE instance_id = ?
                ''',
                (json.dumps(patch), seq, now, instance_id)
            )

            append_event(
                conn,
                instance_id    = instance_id,
                sequence       = seq,
                correlation_id = row['correlation_id'],
                causation_id   = None,
                event_type     = 'domain.patch.proposed',
                payload        = {'patch': patch},
            )

            return jsonify({'ok': True, 'sequence': seq})


    # ── POST /instances/<id>/validate ─────────────────────────────────────────
    @app.route('/instances/<instance_id>/validate', methods=['POST'])
    def validate_patch(instance_id):
        with get_db() as conn:
            row = _get_instance(conn, instance_id)
            if row is None:
                return jsonify({'error': f'INSTANCE_NOT_FOUND: {instance_id}'}), 404

            if not row['proposed_patch']:
                return jsonify({'error': 'NO_PROPOSED_PATCH'}), 400

            payload = json.loads(row['payload'])
            patch   = json.loads(row['proposed_patch'])

            try:
                result = run_python_validation(payload, patch)
            except Exception as e:
                return jsonify({'error': f'VALIDATION_ERROR: {e}'}), 500

            seq    = row['event_sequence'] + 1
            now    = _now()
            passed = result['valid']

            new_state    = 'PATCHED' if passed else 'BLOCKED'
            block_reason = result.get('block_reason') if not passed else None

            conn.execute(
                '''
                UPDATE instances
                SET state          = ?,
                    block_reason   = ?,
                    event_sequence = ?,
                    updated_at     = ?
                WHERE instance_id = ?
                ''',
                (new_state, block_reason, seq, now, instance_id)
            )

            append_event(
                conn,
                instance_id    = instance_id,
                sequence       = seq,
                correlation_id = row['correlation_id'],
                causation_id   = None,
                event_type     = 'domain.validation.passed' if passed else 'domain.validation.failed',
                payload        = result,
            )

            row = _get_instance(conn, instance_id)
            return jsonify({
                'state':      new_state,
                'validation': result,
                'instance':   _serialize_instance(row, conn),
            })


    # ── POST /instances/<id>/accept ───────────────────────────────────────────
    @app.route('/instances/<instance_id>/accept', methods=['POST'])
    def accept_patch(instance_id):
        with get_db() as conn:
            row = _get_instance(conn, instance_id)
            if row is None:
                return jsonify({'error': f'INSTANCE_NOT_FOUND: {instance_id}'}), 404

            if row['state'] == 'RETURNED_TO_CREATE':
                return jsonify(_serialize_instance(row, conn)), 200
            if row['state'] != 'PATCHED':
                return jsonify({
                    'error': f'INVALID_STATE: expected PATCHED, got {row["state"]}'
                }), 409

            if not row['proposed_patch']:
                return jsonify({'error': 'NO_PROPOSED_PATCH'}), 400

            patch = json.loads(row['proposed_patch'])

            write_result = write_patch_to_notion(row['notion_page_id'], patch)

            seq = row['event_sequence'] + 1
            now = _now()

            if write_result.get('success'):
                new_state  = 'RETURNED_TO_CREATE'
                event_type = 'domain.patch.accepted'
            else:
                new_state  = 'VERSION_CONFLICT'
                event_type = 'domain.version.conflict'

            conn.execute(
                '''
                UPDATE instances
                SET state          = ?,
                    event_sequence = ?,
                    updated_at     = ?
                WHERE instance_id = ?
                ''',
                (new_state, seq, now, instance_id)
            )

            append_event(
                conn,
                instance_id    = instance_id,
                sequence       = seq,
                correlation_id = row['correlation_id'],
                causation_id   = None,
                event_type     = event_type,
                payload        = {'write_result': write_result, 'patch': patch},
            )

            if not write_result.get('success'):
                return jsonify({
                    'error': f'NOTION_WRITE_FAIL: {write_result.get("error")}'
                }), 502

            row = _get_instance(conn, instance_id)
            return jsonify(_serialize_instance(row, conn))


    # ── POST /instances/<id>/sync ─────────────────────────────────────────────
    @app.route('/instances/<instance_id>/sync', methods=['POST'])
    def sync_instance(instance_id):
        with get_db() as conn:
            row = _get_instance(conn, instance_id)
            if row is None:
                return jsonify({'error': f'INSTANCE_NOT_FOUND: {instance_id}'}), 404

            try:
                fresh_payload = fetch_notion_page(row['notion_page_id'])
            except Exception as e:
                return jsonify({'error': f'NOTION_FETCH_FAIL: {e}'}), 502

            seq = row['event_sequence'] + 1
            now = _now()

            conn.execute(
                '''
                UPDATE instances
                SET payload        = ?,
                    event_sequence = ?,
                    updated_at     = ?
                WHERE instance_id = ?
                ''',
                (json.dumps(fresh_payload), seq, now, instance_id)
            )

            append_event(
                conn,
                instance_id    = instance_id,
                sequence       = seq,
                correlation_id = row['correlation_id'],
                causation_id   = None,
                event_type     = 'system.sync.completed',
                payload        = {'payload': fresh_payload},
            )

            row = _get_instance(conn, instance_id)
            return jsonify({
                'payload':  fresh_payload,
                'instance': _serialize_instance(row, conn),
            })


    # ── POST /instances/<id>/archive ──────────────────────────────────────────
    @app.route('/instances/<instance_id>/archive', methods=['POST'])
    def archive_instance(instance_id):
        with get_db() as conn:
            row = _get_instance(conn, instance_id)
            if row is None:
                return jsonify({'error': f'INSTANCE_NOT_FOUND: {instance_id}'}), 404

            if row['state'] == 'RETURNED_TO_CREATE':
                return jsonify({
                    'error': 'INVALID_STATE: cannot archive RETURNED_TO_CREATE'
                }), 409

            # Archivar = poner Next_Action = 'Archivar' en Notion
            # (campo correcto: Next_Action, no Status)
            write_result = write_patch_to_notion(
                row['notion_page_id'],
                {'next_action': 'Archivar'}
            )

            seq = row['event_sequence'] + 1
            now = _now()

            conn.execute(
                '''
                UPDATE instances
                SET state          = 'FAILED',
                    event_sequence = ?,
                    updated_at     = ?
                WHERE instance_id = ?
                ''',
                (seq, now, instance_id)
            )

            append_event(
                conn,
                instance_id    = instance_id,
                sequence       = seq,
                correlation_id = row['correlation_id'],
                causation_id   = None,
                event_type     = 'domain.instance.archived',
                payload        = {'write_result': write_result},
            )

            row = _get_instance(conn, instance_id)
            return jsonify(_serialize_instance(row, conn))
