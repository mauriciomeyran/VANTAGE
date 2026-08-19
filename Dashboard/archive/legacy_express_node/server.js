'use strict';

const express = require('express');
const cors    = require('cors');
const https   = require('https');
const path    = require('path');

// ── CONFIG ────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;

const NOTION_TOKEN =
  process.env.NOTION_TOKEN ||
  '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';

const NOTION_DB_ID =
  process.env.NOTION_DB_ID ||
  'b14cc6fc01514c228b11690162236107';

const NOTION_VERSION = '2022-06-28';

// ── DASHBOARD FILENAME ────────────────────────────────────
// Update this when the dashboard version changes.
const DASHBOARD_FILE = 'jhs_dashboard_v7.html';

// ── EXPRESS SETUP ─────────────────────────────────────────
const app = express();

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));

// ── NOTION HTTP HELPER ────────────────────────────────────
function notionRequest(pathname, body = null, method = null) {
  return new Promise((resolve, reject) => {

    const payload = body ? JSON.stringify(body) : null;

    const options = {
      hostname: 'api.notion.com',
      path:     pathname,
      method:   method || (body ? 'POST' : 'GET'),
      headers: {
        Authorization:    `Bearer ${NOTION_TOKEN}`,
        'Notion-Version': NOTION_VERSION,
        'Content-Type':   'application/json',
      }
    };

    if (payload) {
      options.headers['Content-Length'] = Buffer.byteLength(payload);
    }

    const req = https.request(options, res => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (res.statusCode >= 400) { reject(json); return; }
          resolve(json);
        } catch (err) {
          reject(err);
        }
      });
    });

    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

// ── NOTION PROPERTY EXTRACTORS ────────────────────────────
const getText     = p => p?.title?.length     ? p.title.map(t => t.plain_text).join('')
                       : p?.rich_text?.length  ? p.rich_text.map(t => t.plain_text).join('')
                       : '';
const getSelect   = p => p?.select?.name   || '';
const getCheckbox = p => !!p?.checkbox;
const getNumber   = p => p?.number         || 0;
const getDate     = p => p?.date?.start    || '';
const getUrl      = p => p?.url            || '';

// ── VACANCY MAPPER ────────────────────────────────────────
function mapVacancy(page) {
  const p = page.properties;
  return {
    id:           page.id,
    sourceType: getSelect(p['Source_Type']) || getText(p['Source_Type']),
    roleClass:    getSelect(p['Role_Class'])   || getText(p['Role_Class']),
    gateDecision: getSelect(p['Gate_Decision'])|| getText(p['Gate_Decision']),
    nextAction:   getSelect(p['Next_Action'])  || getText(p['Next_Action']),
    priority:     getNumber(p['Prioridad']),
    score:        getNumber(p['Score']),
    status:       getSelect(p['Status'])       || getText(p['Status']),
    role:         getText(p['Rol']),
    brand:        getText(p['Marca']),
    holding:      getText(p['Holding']),
    jobId:        getText(p['JOB_ID']),
    scope:        getSelect(p['VM_Scope'])     || getText(p['VM_Scope']),
    match:        getSelect(p['Match'])        || getText(p['Match']),
    entropy:      getSelect(p['Fetch'])        || getText(p['Fetch']),
    url:          getUrl(p['URL']),
    jd:           getText(p['JD']),
    blockers:     getText(p['Risk Flags']),
    applied:      getCheckbox(p['Applied']),
    nad:          getDate(p['NAD']),
    lastSeen:     getDate(p['Last_Seen_Active']),
    lastTouch:    getDate(p['Last_In-Touch']),
    interviewDate:getDate(p['Interview_Date']),
    contact:      getText(p['Contacto']),
    notes:        getText(p['Notas']),
    source:       getText(p['Fuente']),
  };
}

// ── GET /api/vacancies ────────────────────────────────────
app.get('/api/vacancies', async (req, res) => {
  try {
    const notion = await notionRequest(
      `/v1/databases/${NOTION_DB_ID}/query`,
      { page_size: 100 }
    );

    const vacancies = notion.results.map(mapVacancy);

    const metrics = {
      total:    vacancies.length,
      critical: vacancies.filter(v => (v.blockers || '').toLowerCase().includes('critical')).length,
      ready:    vacancies.filter(v => ['ready','postulado','applied'].includes((v.status || '').toLowerCase())).length,
      blocked:  vacancies.filter(v => ['blocked','bloqueado'].includes((v.status || '').toLowerCase())).length,
    };

    res.json({ ok: true, metrics, vacancies });

  } catch (err) {
    console.error('[NOTION ERROR]', err);
    res.status(500).json({ ok: false, error: err.message || err });
  }
});

// ── PATCH /api/vacancies/:id/status ──────────────────────
app.patch('/api/vacancies/:id/status', async (req, res) => {
  const { id } = req.params;
  const { status } = req.body;
  if (!status) return res.status(400).json({ ok: false, error: 'status required' });
  try {
    await notionRequest(`/v1/pages/${id}`, {
      properties: { Status: { select: { name: status } } }
    }, 'PATCH');
    res.json({ ok: true, id, status });
  } catch (err) {
    console.error('[PATCH status]', err);
    res.status(500).json({ ok: false, error: err.message || err });
  }
});

// ── PATCH /api/vacancies/:id/nad ─────────────────────────
app.patch('/api/vacancies/:id/nad', async (req, res) => {
  const { id } = req.params;
  const { nad } = req.body;
  if (!nad) return res.status(400).json({ ok: false, error: 'nad required' });
  try {
    await notionRequest(`/v1/pages/${id}`, {
      properties: { NAD: { date: { start: nad } } }
    }, 'PATCH');
    res.json({ ok: true, id, nad });
  } catch (err) {
    console.error('[PATCH nad]', err);
    res.status(500).json({ ok: false, error: err.message || err });
  }
});

// ── PATCH /api/vacancies/:id/depurar ─────────────────────
app.patch('/api/vacancies/:id/depurar', async (req, res) => {
  const { id } = req.params;
  try {
    await notionRequest(`/v1/pages/${id}`, {
      properties: {
        Status:  { select:   { name: 'Expirada' } },
        Depurar: { checkbox: true }
      }
    }, 'PATCH');
    res.json({ ok: true, id, action: 'depurado' });
  } catch (err) {
    console.error('[PATCH depurar]', err);
    res.status(500).json({ ok: false, error: err.message || err });
  }
});

// ── ROOT REDIRECT ─────────────────────────────────────────
app.get('/', (_, res) => res.redirect(`/${DASHBOARD_FILE}`));

// ── START ─────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log('');
  console.log(`JHS Server       → http://localhost:${PORT}`);
  console.log(`Dashboard        → http://localhost:${PORT}/${DASHBOARD_FILE}`);
  console.log(`Vacancies API    → http://localhost:${PORT}/api/vacancies`);
  console.log('');
});
