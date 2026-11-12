const USERS={'aluno@portal.com':{nome:'Ana Beatriz Lima',papel:'aluno',mat:'2024102345',curso:'Análise e Desenvolvimento de Sistemas',per:'4º período',tel:'(83) 98877-1020'},
'secretaria@portal.com':{nome:'Marcos Oliveira',papel:'admin'}};
const DISC=[
{c:'ADS201',n:'Banco de Dados',p:'Carlos Menezes',h:'Seg e Qua, 19h',ch:60,n1:8.5,n2:7.5,f:2},
{c:'ADS202',n:'Engenharia de Software',p:'Juliana Reis',h:'Ter e Qui, 19h',ch:60,n1:9,n2:8,f:0},
{c:'ADS203',n:'Programação Web',p:'Rafael Tavares',h:'Qua, 21h',ch:40,n1:6,n2:5.5,f:4},
{c:'ADS204',n:'Redes de Computadores',p:'Paulo Sérgio',h:'Sex, 19h',ch:40,n1:7.5,n2:null,f:1}];
const AVISOS=[
{t:'Prazo de rematrícula prorrogado',d:'03/11/2026',imp:1,x:'A rematrícula do próximo período vai até 20/11. Procure a secretaria em caso de pendências.'},
{t:'Semana de provas da N2',d:'30/10/2026',x:'As avaliações da N2 acontecem de 09 a 13/11, nos horários habituais das aulas.'},
{t:'Biblioteca com horário estendido',d:'27/10/2026',x:'Até o fim do semestre a biblioteca fecha às 22h, de segunda a sexta.'}];
const TIPOS=['Declaração de matrícula','Declaração de vínculo','Histórico escolar','Comprovante de conclusão'];
const ST={pend:['Pendente','t-warn'],and:['Em andamento','t-info'],ok:['Concluído','t-ok']};
let SOL=[{id:101,tipo:'Declaração de matrícula',data:'28/10/2026',st:'ok',obs:'',aten:'Documento enviado para assinatura na plataforma Eleven.',aluno:'Ana Beatriz Lima',mat:'2024102345'}];
let seq=102,user=null,page='dash';

const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const media=d=>d.n2==null?null:(d.n1+d.n2)/2;
const sit=d=>{const m=media(d);return m==null?['Em andamento','t-info']:m>=7?['Aprovado','t-ok']:m>=5?['Recuperação','t-warn']:['Reprovado','t-bad']};
const fmt=n=>n==null?'—':n.toFixed(1).replace('.',',');
const hoje=()=>new Date().toLocaleDateString('pt-BR');
function toast(m){const t=$('#toast');t.textContent=m;t.classList.remove('hidden');clearTimeout(toast.k);toast.k=setTimeout(()=>t.classList.add('hidden'),2600)}

$('#lf').addEventListener('submit',e=>{
  e.preventDefault();
  const em=$('#em').value.trim().toLowerCase(),pw=$('#pw').value,er=$('#lerr');
  if(!em||!pw){er.textContent='Preencha e-mail e senha.';er.classList.remove('hidden');return}
  if(!USERS[em]||pw!=='123456'){er.textContent='E-mail ou senha incorretos. Confira os dados e tente de novo.';er.classList.remove('hidden');return}
  user=USERS[em];er.classList.add('hidden');$('#pw').value='';
  $('#login').classList.add('hidden');$('#app').classList.remove('hidden');
  $('#uname').textContent=user.nome;$('#urole').textContent=user.papel==='aluno'?user.mat:'Secretaria acadêmica';
  $('#ini').textContent=user.nome.split(' ').map(w=>w[0]).slice(0,2).join('');
  go(user.papel==='aluno'?'dash':'sols');
});
$('#out').onclick=()=>{user=null;$('#app').classList.add('hidden');$('#login').classList.remove('hidden');$('#em').value='';toast('Você saiu do portal.')};

const MENU={aluno:[['dash','Início'],['disc','Disciplinas'],['notas','Notas'],['avisos','Avisos'],['docs','Documentos'],['dados','Dados pessoais']],
admin:[['sols','Solicitações'],['avisos','Avisos']]};
function go(p){
  page=p;
  $('#nav').innerHTML=MENU[user.papel].map(([k,l])=>`<button class="nav" data-p="${k}" ${k===p?'aria-current="page"':''}>${l}</button>`).join('');
  $('#nav').querySelectorAll('.nav').forEach(b=>b.onclick=()=>go(b.dataset.p));
  const R=VIEWS[p];$('#title').textContent=R.t;$('#view').innerHTML=R.r();if(R.b)R.b();
  scrollTo(0,0);
}
const avisoHtml=a=>`<article class="card aviso ${a.imp?'imp':''}"><h3>${a.t}</h3><div class="mut">${a.d}</div><p style="margin:8px 0 0">${a.x}</p></article>`;
const stTag=s=>`<span class="tag ${ST[s][1]}">${ST[s][0]}</span>`;
const minhas=()=>SOL.filter(s=>s.mat===user.mat);

const VIEWS={
dash:{t:'Olá, '+'Ana',r:()=>{
  const ms=DISC.map(media).filter(m=>m!=null),mg=ms.reduce((a,b)=>a+b,0)/ms.length,fa=DISC.reduce((a,d)=>a+d.f,0),ab=minhas().filter(s=>s.st!=='ok').length;
  return `<div class="grid">
  <div class="card stat"><b>${DISC.length}</b><span>disciplinas neste período</span></div>
  <div class="card stat"><b>${fmt(mg)}</b><span>média geral até agora</span></div>
  <div class="card stat"><b>${fa}</b><span>faltas registradas</span></div>
  <div class="card stat"><b>${ab}</b><span>solicitações em aberto</span></div></div>
  <h2 style="margin:26px 0 12px">Avisos recentes</h2><div class="stack">${AVISOS.slice(0,2).map(avisoHtml).join('')}</div>
  <h2 style="margin:26px 0 12px">Suas aulas</h2><div class="card tw"><table><tbody>${DISC.map(d=>`<tr><td><b>${d.n}</b></td><td>${d.h}</td><td class="mut">Prof. ${d.p}</td></tr>`).join('')}</tbody></table></div>`}},
disc:{t:'Disciplinas',r:()=>`<div class="grid">${DISC.map(d=>`<article class="card"><h3>${d.n}</h3><div class="mut">${d.c} · ${d.ch}h</div><dl class="dl" style="margin-top:12px;grid-template-columns:90px 1fr"><dt>Professor</dt><dd>${d.p}</dd><dt>Horário</dt><dd>${d.h}</dd><dt>Faltas</dt><dd>${d.f}</dd></dl></article>`).join('')}</div>`},
notas:{t:'Notas',r:()=>`<div class="card tw"><table><thead><tr><th>Disciplina</th><th>N1</th><th>N2</th><th>Média</th><th>Situação</th></tr></thead><tbody>${DISC.map(d=>{const s=sit(d);return `<tr><td>${d.n}</td><td>${fmt(d.n1)}</td><td>${fmt(d.n2)}</td><td><b>${fmt(media(d))}</b></td><td><span class="tag ${s[1]}">${s[0]}</span></td></tr>`}).join('')}</tbody></table></div><p class="hint">Aprovação com média 7,0 ou mais. Notas oficiais seguem o sistema acadêmico da instituição.</p>`},
avisos:{t:'Avisos',r:()=>`<div class="stack">${AVISOS.map(avisoHtml).join('')}</div>`},
docs:{t:'Documentos',r:()=>`<form class="card stack" id="df"><h2>Solicitar documento</h2>
  <div class="row"><label>Tipo de documento<select id="dt">${TIPOS.map(t=>`<option>${t}</option>`).join('')}</select></label>
  <label>Finalidade<select id="df2"><option>Estágio</option><option>Trabalho</option><option>Bolsa ou financiamento</option><option>Outra</option></select></label></div>
  <label>Observações (opcional)<textarea id="do"></textarea></label>
  <div><button class="btn" type="submit">Enviar solicitação</button></div>
  <p class="hint">A assinatura dos documentos é feita pela plataforma Eleven, após a análise da secretaria.</p></form>
  <h2 style="margin:26px 0 12px">Minhas solicitações</h2><div class="card tw" id="dl"></div>`,
 b:()=>{
  const draw=()=>{const l=minhas().slice().reverse();$('#dl').innerHTML=l.length?`<table><thead><tr><th>Protocolo</th><th>Documento</th><th>Data</th><th>Situação</th><th>Retorno da secretaria</th></tr></thead><tbody>${l.map(s=>`<tr><td>#${s.id}</td><td>${s.tipo}</td><td>${s.data}</td><td>${stTag(s.st)}</td><td class="mut">${s.aten?esc(s.aten):'Aguardando análise'}</td></tr>`).join('')}</tbody></table>`:'<p class="mut" style="padding:12px">Você ainda não fez solicitações. Use o formulário acima para pedir o primeiro documento.</p>'};
  draw();
  $('#df').addEventListener('submit',e=>{e.preventDefault();
   SOL.push({id:seq++,tipo:$('#dt').value,fin:$('#df2').value,data:hoje(),st:'pend',obs:$('#do').value.trim(),aten:'',aluno:user.nome,mat:user.mat});
   $('#do').value='';draw();toast('Solicitação enviada. Acompanhe o andamento abaixo.')})}},
dados:{t:'Dados pessoais',r:()=>`<div class="card"><dl class="dl"><dt>Nome</dt><dd>${user.nome}</dd><dt>Matrícula</dt><dd>${user.mat}</dd><dt>Curso</dt><dd>${user.curso}</dd><dt>Período</dt><dd>${user.per}</dd><dt>E-mail</dt><dd>aluno@portal.com</dd><dt>Telefone</dt><dd>${user.tel}</dd></dl></div><p class="hint">Para corrigir algum dado, solicite a atualização na secretaria.</p>`},
sols:{t:'Solicitações de documentos',r:()=>`<div class="card tw" id="sl"></div>`,
 b:()=>{
  const draw=()=>{$('#sl').innerHTML=`<table style="min-width:760px"><thead><tr><th>Protocolo</th><th>Solicitante</th><th>Documento</th><th>Data</th><th>Situação</th><th></th></tr></thead><tbody>${SOL.slice().reverse().map(s=>`<tr><td>#${s.id}</td><td>${esc(s.aluno)}<div class="mut">Mat. ${s.mat}</div></td><td>${s.tipo}${s.fin?`<div class="mut">${s.fin}</div>`:''}</td><td>${s.data}</td><td>${stTag(s.st)}</td><td><button class="btn ghost" data-id="${s.id}">Atender</button></td></tr>`).join('')}</tbody></table>`;
   $('#sl').querySelectorAll('button').forEach(b=>b.onclick=()=>open(+b.dataset.id))};
  const open=id=>{const s=SOL.find(x=>x.id===id);
   $('#sl').innerHTML=`<form class="stack" id="af"><h2>Protocolo #${s.id} · ${s.tipo}</h2>
   <dl class="dl"><dt>Solicitante</dt><dd>${esc(s.aluno)} (mat. ${s.mat})</dd><dt>Data</dt><dd>${s.data}</dd><dt>Observação do aluno</dt><dd>${s.obs?esc(s.obs):'—'}</dd></dl>
   <label>Situação<select id="as">${Object.entries(ST).map(([k,v])=>`<option value="${k}" ${k===s.st?'selected':''}>${v[0]}</option>`).join('')}</select></label>
   <label>Registro de atendimento<textarea id="an">${esc(s.aten)}</textarea></label>
   <div class="row" style="justify-content:flex-start"><button class="btn" type="submit" style="flex:0">Salvar</button><button class="btn ghost" type="button" id="ac" style="flex:0">Voltar</button></div></form>`;
   $('#ac').onclick=draw;
   $('#af').addEventListener('submit',e=>{e.preventDefault();s.st=$('#as').value;s.aten=$('#an').value.trim();toast('Atendimento salvo.');draw()})};
  draw()}}
};
