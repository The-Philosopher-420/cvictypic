// Mock GitHub Contents API (len čo appka používa): GET file/dir, PUT s kontrolou sha, 404/409/422
const http=require('http'),crypto=require('crypto');
const files={}; // path -> content (string)
const sha=t=>crypto.createHash('sha1').update('blob '+Buffer.byteLength(t)+'\0'+t).digest('hex');
let log=[];
const srv=http.createServer((req,res)=>{
 let body='';req.on('data',c=>body+=c);req.on('end',()=>{
  const u=new URL(req.url,'http://x');const m=u.pathname.match(/^\/repos\/([^/]+)\/([^/]+)(?:\/contents\/(.*))?$/);
  const send=(code,obj)=>{if(code>=400&&code!==404)log.push('  -> '+code);res.writeHead(code,{'Content-Type':'application/json','Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'GET,PUT,DELETE,OPTIONS'});res.end(obj===undefined?'':JSON.stringify(obj));};
  if(req.method==='OPTIONS')return send(204);
  if(u.pathname==='/__dump')return send(200,{files,log});
  if(u.pathname==='/__reset'){for(const k in files)delete files[k];log=[];return send(200,{ok:1});}
  if(!m)return send(404,{message:'nf'});
  if(!req.headers.authorization||!req.headers.authorization.startsWith('Bearer '))return send(401,{message:'auth'});
  const p=m[3];log.push(req.method+' '+(p||'(repo)'));
  if(p===undefined)return send(200,{name:m[2]});
  if(req.method==='GET'){
   if(files[p]!==undefined)return send(200,{type:'file',name:p.split('/').pop(),path:p,sha:sha(files[p]),content:Buffer.from(files[p]).toString('base64')});
   const dir=p.replace(/\/$/,'')+'/';const list=Object.keys(files).filter(k=>k.startsWith(dir)&&!k.slice(dir.length).includes('/')).map(k=>({type:'file',name:k.slice(dir.length),path:k,sha:sha(files[k])}));
   if(list.length)return send(200,list);return send(404,{message:'Not Found'});
  }
  if(req.method==='PUT'){const j=JSON.parse(body||'{}');const content=Buffer.from(j.content||'','base64').toString();
   if(files[p]!==undefined){if(!j.sha)return send(422,{message:'sha missing'});if(j.sha!==sha(files[p]))return send(409,{message:'sha mismatch'});files[p]=content;return send(200,{content:{sha:sha(content)}});}
   if(j.sha)return send(422,{message:'file does not exist'});files[p]=content;return send(201,{content:{sha:sha(content)}});}
  send(405,{message:'m'});
 });
});
srv.listen(8766,'127.0.0.1',()=>console.log('mock gh on 8766'));
