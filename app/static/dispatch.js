const status = document.querySelector('#dispatch-message');

async function post(path,body) {
  const response = await fetch(path, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || '交班提交失败');
  return data;
}

function bind(selector, submit) {
  const form = document.querySelector(selector);
  form?.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button');
    button.disabled = true;
    status.textContent = '正在核量…';
    try { await submit(form); }
    catch (error) { status.textContent = error.message; }
    finally { button.disabled = false; }
  });
}

bind('#archive', async form => {
  const files = Object.fromEntries(['tickets','receipts','stock'].map(id => [id,document.getElementById(id).value]));
  const values = Object.values(files);
  if (values.some(Boolean) && !values.every(Boolean)) throw new Error('请填全三份 CSV');
  const sample = form.dataset.sample;
  const ack = await post('/api/shifts', values.every(Boolean) ? files : {sample});
  location.assign('/ops/sign?' + new URLSearchParams({sample,batch:ack.batch}));
});

const pick = document.querySelector('#batch');
const hash = document.querySelector('#checksum');
const exportLink = document.querySelector('#export-slip');
pick?.addEventListener('change', () => { hash.value = ''; exportLink.hidden = true; });
bind('#signature', async () => {
  const batch = pick.value;
  const result = await post(`/api/shifts/${batch}/sign`,{});
  if (pick.value !== batch) return;
  hash.value = result.checksum;
  exportLink.href = `/api/shifts/${batch}/export`;
  exportLink.hidden = false;
  status.textContent = `证据已签发 · 待复核 ${result.open_items} 票`;
});

bind('#returns-form', async form => {
  const lines = document.getElementById('return-lines').value.split('\n').map(line => line.trim()).filter(Boolean);
  if (!lines.length) throw new Error('请填写退油单');
  const returns = lines.map(line => {
    const cells = line.split(',').map(cell => cell.trim());
    if (cells.length !== 5 || cells.some(cell => !cell)) throw new Error('退油单格式：退油单号,原票号,接收罐车,磅单号,过磅 kg');
    const [return_id,ticket,truck,weighbill,kg] = cells;
    return {return_id,ticket,truck,weighbill,kg};
  });
  await post('/api/returns',{sample:form.dataset.sample,returns});
  location.reload();
});

document.querySelectorAll('[data-return-action]').forEach(button => {
  button.addEventListener('click', async () => {
    button.disabled = true;
    const id = button.dataset.returnId, action = button.dataset.returnAction;
    try {
      const result = await post(`/api/returns/${encodeURIComponent(id)}/${action}`,{sample:button.dataset.sample || 'dirty'});
      if (action === 'voucher') {
        status.textContent = `凭证 ${result.checksum.slice(0,16)}… · ${result.voucher.writeoff.status === 'CONFIRMED' ? '已冲销' : '冲销待核'}`;
      } else {
        location.reload();
      }
    } catch (error) { status.textContent = error.message; }
    finally { button.disabled = false; }
  });
});
