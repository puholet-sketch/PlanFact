
// Вставьте в консоль на https://portal.virtusystems.ru (авторизованы)
(async () => {
  const keys = ["RGS-16634", "RGS-20056", "RGS-20414", "RGS-20469", "RGS-20470", "RGS-20574", "RGS-20620", "RGS-20688", "RGS-20709", "RGS-20710", "RGS-20715", "RGS-20747", "RGS-20774", "RGS-20777", "RGS-20786", "RGS-20787", "RGS-20793", "RGS-20796", "RGS-20798", "RGS-20806", "RGS-20809", "RGS-20818", "RGS-20834", "RGS-20837", "RGS-20843", "RGS-20845", "RGS-20883", "RGS-20885", "RGS-20939", "RGS-20940", "RGS-20944", "RGS-20967", "RGS-20968", "RGS-20975", "RGS-20989", "RGS-21002", "RGS-21030", "RGS-21076", "RGS-21113", "RGS-21114", "RGS-21118", "RGS-21127", "RGS-21150", "RGS-21154", "RGS-21259", "RGS-21261", "RGS-21277", "SOGLVFOS-1456"];
  const out = {};
  for (const key of keys) {
    const r = await fetch('/rest/api/2/issue/' + key + '?fields=summary,issuetype,parent,timeoriginalestimate,timespent');
    const j = await r.json();
    let siblings = [];
    const parent = j.fields && j.fields.parent && j.fields.parent.key;
    if (parent) {
      const pr = await fetch('/rest/api/2/issue/' + parent + '?fields=subtasks');
      const pj = await pr.json();
      siblings = (pj.fields.subtasks || []).map(s => ({
        key: s.key, summary: s.fields.summary, type: s.fields.issuetype.name
      }));
    }
    out[key] = {
      key, summary: j.fields.summary, type: j.fields.issuetype.name, parent,
      origEstH: (j.fields.timeoriginalestimate || 0) / 3600,
      spentH: (j.fields.timespent || 0) / 3600,
      siblings
    };
    console.log('done', key);
  }
  copy(JSON.stringify(out, null, 2));
  console.log('JSON скопирован в буфер — сохраните в jira_audit_cache.json');
  return out;
})();
