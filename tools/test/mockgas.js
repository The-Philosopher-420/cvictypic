/* Mock Google Apps Script web app (port 8767): spúšťa skutočný tools/server/Code.gs nad shimmi služieb a odpovedá ako GAS
   (POST → 302 presmerovanie na jednorazovú adresu s JSON výstupom, CORS *). Spustenie: node tools/test/mockgas.js */
const http=require('http'),zlib=require('zlib'),crypto=require('crypto'),fs=require('fs'),path=require('path');
const props={};
global.PropertiesService={getScriptProperties:()=>({getProperty:k=>props[k]===undefined?null:props[k],setProperties:(o)=>Object.assign(props,o),deleteProperty:k=>{delete props[k];}})};
class Blob{constructor(b){this.b=Buffer.isBuffer(b)?b:Buffer.from(b,'utf8');}getBytes(){return [...this.b];}getDataAsString(){return this.b.toString('utf8');}}
global.Utilities={newBlob:(b)=>new Blob(Buffer.isBuffer(b)?b:(Array.isArray(b)?Buffer.from(b):Buffer.from(b,'utf8'))),gzip:bl=>new Blob(zlib.gzipSync(bl.b)),ungzip:bl=>new Blob(zlib.gunzipSync(bl.b)),base64Encode:bytes=>Buffer.from(bytes).toString('base64'),base64Decode:s=>[...Buffer.from(s,'base64')],computeDigest:(a,t)=>[...crypto.createHash('sha1').update(t,'utf8').digest()].map(b=>b>127?b-256:b),DigestAlgorithm:{SHA_1:1},Charset:{UTF_8:1}};
global.LockService={getScriptLock:()=>({waitLock(){},releaseLock(){}})};
global.ContentService={createTextOutput:s=>({s,setMimeType(){return this;}}),MimeType:{JSON:1}};
eval(fs.readFileSync(path.join(__dirname,'..','server','Code.gs'),'utf8'));
const pending={};let seq=0;
http.createServer((req,res)=>{
 const u=new URL(req.url,'http://x');
 const cors={'Access-Control-Allow-Origin':'*'};
 if(req.method==='OPTIONS'){res.writeHead(204,Object.assign({'Access-Control-Allow-Methods':'GET,POST','Access-Control-Allow-Headers':'*'},cors));res.end();return;}
 if(u.pathname==='/exec'&&req.method==='POST'){let b='';req.on('data',c=>b+=c);req.on('end',()=>{const out=doPost({postData:{contents:b}}).s;const id=String(++seq);pending[id]=out;res.writeHead(302,Object.assign({Location:'/out/'+id},cors));res.end();});return;}
 if(u.pathname==='/exec'&&req.method==='GET'){const out=doGet({parameter:Object.fromEntries(u.searchParams)}).s;res.writeHead(200,Object.assign({'Content-Type':'application/json'},cors));res.end(out);return;}
 if(u.pathname.startsWith('/out/')){const out=pending[u.pathname.slice(5)];delete pending[u.pathname.slice(5)];res.writeHead(out?200:404,Object.assign({'Content-Type':'application/json'},cors));res.end(out||'{}');return;}
 if(u.pathname==='/_reset'){for(const k of Object.keys(props))delete props[k];res.writeHead(200,cors);res.end('ok');return;}
 if(u.pathname==='/_props'){res.writeHead(200,Object.assign({'Content-Type':'application/json'},cors));res.end(JSON.stringify({keys:Object.keys(props),bytes:Object.values(props).join('').length}));return;}
 res.writeHead(404);res.end();
}).listen(8767,'127.0.0.1',()=>console.log('mock GAS on 8767'));
