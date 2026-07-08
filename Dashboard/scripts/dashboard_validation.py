from layer_1_run import (
    validate_url_pre_ingestion,
    calculate_score_v6,
    get_vm_scope,
    get_role_class,
    gate,
)


def run_python_validation(current_payload: dict, patch: dict):
    merged = {**current_payload, **patch}

    rol         = merged.get('rol', '')
    marca       = merged.get('marca', '')
    url         = merged.get('url', '')
    source_type = merged.get('source_type', 'Vacante')
    jd          = merged.get('jd', '')

    bypass_types = {
        'Inbound',
        'Referencia',
        'Networking',
    }

    if source_type in bypass_types:
        fetch_status = 'Accesible'
        url_valid    = True
        url_reason   = 'BYPASS_SOURCE_TYPE'

    elif not url:
        fetch_status = 'Bloqueado'
        url_valid    = False
        url_reason   = 'MISSING_URL'

    else:
        url_valid, url_reason = validate_url_pre_ingestion(url, jd)
        fetch_status = 'Accesible' if url_valid else 'Bloqueado'

    entry_data = {
        'title': rol,
        'company': marca,
        'jd': jd,
        'contact': merged.get('contacto', ''),
    }

    score      = calculate_score_v6(entry_data)
    vm_scope   = get_vm_scope(rol)
    role_class = get_role_class(rol)
    fuente     = merged.get('fuente', '') or 'Career Page Oficial'

    gate_decision = gate(
        fetch_status,
        vm_scope,
        role_class,
        source_type,
    )

    block_reason = None

    if gate_decision == 'BLOCKED':
        reasons = []

        if not url_valid:
            reasons.append(f'URL_GATE_FAIL:{url_reason}')

        if vm_scope != 'Alto' and role_class not in ('VM', 'Pivote'):
            reasons.append(
                f'SCOPE_MISMATCH:vm_scope={vm_scope},role_class={role_class}'
            )

        block_reason = (
            ' | '.join(reasons)
            if reasons
            else 'GATE_CRITERIA_NOT_MET'
        )

    return {
        'valid': gate_decision == 'CREATE',
        'gate_decision': gate_decision,
        'score': score,
        'vm_scope': vm_scope,
        'role_class': role_class,
        'fetch_status': fetch_status,
        'fuente': fuente,
        'block_reason': block_reason,
        'url_reason': url_reason,
        'next_version_id': (
            current_payload.get('_version_id', 1) or 1
        ) + 1,
    }
