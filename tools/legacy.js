/* =====================================================================
   MIGRÁCIA STARÝCH LOKÁLNYCH DÁT (v1–v4 v localStorage telefónu) → v5 záznamy
   Rovnaký algoritmus ako serverový skript tools/migrate.js. Staré kľúče sa nemažú.
   ===================================================================== */
function mondayOf(s){const [y,m,d]=String(s).split('-').map(Number);const dt=new Date(y,m-1,d);const wd=(dt.getDay()+6)%7;dt.setDate(dt.getDate()-wd);return dt.getFullYear()+'-'+String(dt.getMonth()+1).padStart(2,'0')+'-'+String(dt.getDate()).padStart(2,'0');}
function legacyToWorkouts(d,u,src){
 const out=[];const acts=[];
 (d.logs||[]).forEach(l=>{
  let items=l.items;
  if(!items&&l.ex){items=Object.entries(l.ex).map(([id,sets])=>({id,nm:'',sets:(sets||[]).map((s,i)=>({w:+s[0]||0,r:+s[1]||0,d:i===3?1:0}))}));}
  const lid=String(l.id||(l.date+'-'+l.session));const entries=(items||[]).map((it,i)=>({id:it.k||(lid+':'+i+':'+String(it.id||'x')),exercise_id:String(it.id||'x'),nm:it.nm||'',order:i,sets:(it.sets||[]).map(s=>({w:+s.w||0,r:+s.r||0,d:s.d?1:0})),user_id:u,schema_version:SCHEMA,ts:(l.date||'')+'T00:00'}));
  out.push({id:lid,schema_version:SCHEMA,user_id:u,date:l.date,ts:(l.date||'')+'T00:00',session:SES_META[l.session]?l.session:'X',start:'',end:'',note:l.note||'',entries,src:src+(l.ex?':v1':':v3'),created:l.u||0,updated:l.u||Date.now(),dev:'migr'});
 });
 /* check-in je „UA odcvičené v týždni wk“ – ak v tom týždni existuje meranie UA, check-in je nadbytočný (dátum swipu sa často líši o deň) */
 const logged=new Set(out.map(w=>mondayOf(w.date)+'|'+w.session));
 const actKeys=new Set((d.acts||[]).map(a=>(a.d||'')+'|'+(a.kind||'')));
 Object.entries(d.checks||{}).forEach(([wk,bl])=>Object.entries(bl).forEach(([k,v])=>{
  if(!v||v.s!=='done')return;const date=v.d||wk;const ses=SES_META[k]?k:(v.t==='kardio'?'K':'X');
  if(SES_META[k]&&logged.has(wk+'|'+k))return;
  if(ses==='K'||ses==='X'){if(v.act||actKeys.has(date+'|'+(v.ses||k)))return;acts.push({id:'chk-'+wk+'-'+k,schema_version:SCHEMA,user_id:u,date,ts:date+'T00:00',kind:v.ses||k,min:+v.min||0,note:v.n||'',src:src+':check',updated:Date.now(),dev:'migr'});return;}
  out.push({id:'chk-'+wk+'-'+k,schema_version:SCHEMA,user_id:u,date,week:wk,ts:date+'T00:00',session:ses,start:'',end:'',note:v.note||'',entries:[],src:'check',updated:Date.now(),dev:'migr'});
 }));
 (d.acts||[]).forEach(a=>acts.push({id:String(a.id||('act-'+a.d+'-'+(a.kind||'')+'-'+(a.min||0))),schema_version:SCHEMA,user_id:u,date:a.d,ts:(a.d||'')+'T00:00',kind:a.kind||'OTHER',name:a.name||'',min:+a.min||0,int:a.int||'',note:a.note||'',src:src+':act',updated:a.u||Date.now(),dev:'migr'}));
 return {workouts:out,acts};
}
if(typeof module!=='undefined'&&module.exports)module.exports={legacyToWorkouts,mondayOf};
