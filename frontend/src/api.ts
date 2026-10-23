export async function api<T>(path:string, body?:unknown, method?:string):Promise<T> {
  const response = await fetch('/api'+path,{method:method || (body===undefined?'GET':'POST'),headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
  const result = await response.json().catch(()=>({detail:'서버 응답을 읽지 못했습니다. 서버 실행 상태를 확인해 주세요.'}));
  if(!response.ok) {
    const detail = result.detail;
    throw new Error(typeof detail==='string'?detail:Array.isArray(detail)?detail.map((v:{loc:string[];msg:string})=>`${v.loc.slice(1).join('.')}: ${v.msg}`).join(' / '):'요청을 처리하지 못했습니다. 다시 시도해 주세요.');
  }
  return result;
}
