const API = '/api';

async function api(path, options = {}) {
  const url = `${API}${path}`;
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return resp.json();
}

async function loadDashboard() {
  const data = await api('/dashboard');
  document.getElementById('stats').innerHTML = `
    <div class="stat-card"><div class="label">今日工单</div><div class="value">${data.total_today}</div><div class="sub">全渠道累计</div></div>
    <div class="stat-card"><div class="label">已解决</div><div class="value">${data.resolved_today}</div><div class="sub">自动回复率 ${data.auto_reply_rate}%</div></div>
    <div class="stat-card"><div class="label">待人工处理</div><div class="value">${data.pending_human}</div><div class="sub">需人工介入</div></div>
    <div class="stat-card"><div class="label">平均等待</div><div class="value">${data.avg_wait_minutes}<span style="font-size:16px;"> 分钟</span></div><div class="sub">目标 < 5 分钟</div></div>
    <div class="stat-card"><div class="label">渠道分布</div><div class="value" style="font-size:14px;">${Object.entries(data.by_channel).map(([k,v]) => `${k}: ${v}`).join(' / ')}</div></div>
    <div class="stat-card"><div class="label">紧急工单</div><div class="value" style="color:#c62828;">${data.by_priority?.P0 || 0} <span style="font-size:14px;color:#e65100;">P1: ${data.by_priority?.P1 || 0}</span></div></div>
  `;
}

function statusBadge(status) {
  const map = { new: 'badge-new', classifying: 'badge-auto', auto_replying: 'badge-auto', resolved: 'badge-resolved', pending_human: 'badge-human', human_processing: 'badge-human', closed: 'badge-resolved' };
  return `<span class="badge ${map[status] || ''}">${status}</span>`;
}

function priorityBadge(priority) {
  const map = { P0: 'badge-p0', P1: 'badge-p1', P2: 'badge-p2', P3: 'badge-p3' };
  return `<span class="badge ${map[priority] || ''}">${priority}</span>`;
}

async function loadTickets() {
  const status = document.getElementById('filterStatus').value;
  const channel = document.getElementById('filterChannel').value;
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (channel) params.set('channel', channel);
  params.set('limit', '100');
  const tickets = await api(`/tickets?${params}`);

  if (tickets.length === 0) {
    document.getElementById('ticketList').innerHTML = '<div class="empty">暂无工单</div>';
    return;
  }
  document.getElementById('ticketList').innerHTML = tickets.map(t => `
    <div class="ticket-item" onclick="openDetail(${t.id})">
      <div class="t-info">
        <div class="t-title">${t.title}</div>
        <div class="t-meta">${t.channel} | ${t.customer_name} | ${t.created_at?.slice(0,16)} | ${t.major_category || '未分类'} > ${t.sub_category || ''}</div>
      </div>
      <div>${statusBadge(t.status)}</div>
      <div>${priorityBadge(t.priority)}</div>
      <div class="flex-row">
        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation();quickReply(${t.id})" ${t.status === 'resolved' || t.status === 'closed' ? 'disabled' : ''}>回复</button>
      </div>
    </div>
  `).join('');
}

async function openDetail(ticketId) {
  const ticket = await api(`/tickets/${ticketId}`);
  const msgs = ticket.messages || [];
  const handoff = ticket.handoff;

  document.getElementById('detailContent').innerHTML = `
    <div class="flex-row" style="justify-content:space-between;margin-bottom:16px;">
      <h3>工单 #${ticket.id} — ${ticket.title}</h3>
      <button class="btn btn-outline" onclick="document.getElementById('detailModal').classList.remove('active')">关闭</button>
    </div>
    <div style="margin-bottom:16px;font-size:13px;color:#888;">
      渠道: ${ticket.channel} | 客户: ${ticket.customer_name} | 分类: ${ticket.major_category || '未分类'} > ${ticket.sub_category || ''} | 置信度: ${(ticket.confidence*100).toFixed(0)}% | 状态: ${ticket.status}
    </div>
    ${handoff ? `<div style="background:#fff3e0;padding:12px;border-radius:8px;margin-bottom:12px;font-size:13px;">
      <strong>转人工记录</strong><br>
      情绪: ${handoff.emotion_analysis || '-'} | 预估处理: ${handoff.estimated_minutes}分钟<br>
      建议: ${handoff.suggested_action || '-'}<br>
      技能标签: ${Array.isArray(handoff.matched_skills) ? handoff.matched_skills.join(', ') : (handoff.matched_skills || '-')}
    </div>` : ''}
    <div style="margin-bottom:16px;">
      ${msgs.map(m => `<div class="chat-bubble chat-${m.role}"><strong>${m.role === 'customer' ? '客户' : m.role === 'agent' ? '客服' : '系统'}</strong> <span style="font-size:11px;color:#999;">${m.created_at?.slice(0,16)}</span><br>${m.content.slice(0,300)}</div>`).join('')}
    </div>
    ${ticket.status !== 'resolved' && ticket.status !== 'closed' ? `
      <div class="form-group"><textarea id="replyText" placeholder="输入回复内容（留空则AI自动回复）..."></textarea></div>
      <div class="flex-row" style="justify-content:flex-end;">
        <button class="btn btn-outline" onclick="triggerHandoff(${ticket.id})">转人工</button>
        <button class="btn btn-primary" onclick="triggerReply(${ticket.id})">发送 / AI自动回复</button>
      </div>
    ` : ''}
  `;
  document.getElementById('detailModal').classList.add('active');
}

async function quickReply(ticketId) {
  document.getElementById('detailContent').innerHTML = '<div class="loading">正在生成自动回复...</div>';
  document.getElementById('detailModal').classList.add('active');
  const result = await api(`/tickets/${ticketId}/reply`, { method: 'POST', body: JSON.stringify({ content: '' }) });
  document.getElementById('detailContent').innerHTML = `
    <h3>自动回复 #${ticketId}</h3>
    <div style="white-space:pre-wrap;background:#f9f9f9;padding:16px;border-radius:8px;margin-bottom:12px;font-size:14px;line-height:1.6;">${result.reply}</div>
    <div style="font-size:13px;color:#888;">闭环: ${result.closed ? '已解决' : '待跟进'} | 第 ${result.round} 轮回复</div>
    <button class="btn btn-outline" style="margin-top:12px;" onclick="document.getElementById('detailModal').classList.remove('active');loadTickets();loadDashboard();">关闭</button>
  `;
}

async function triggerReply(ticketId) {
  const text = document.getElementById('replyText').value;
  const result = await api(`/tickets/${ticketId}/reply`, { method: 'POST', body: JSON.stringify({ content: text }) });
  openDetail(ticketId);
  loadDashboard();
}

async function triggerHandoff(ticketId) {
  const result = await api(`/tickets/${ticketId}/handoff`, { method: 'POST' });
  alert(`已转人工\n情绪: ${result.emotion}\n建议: ${result.suggested_actions}\n预估: ${result.estimated_minutes}分钟`);
  openDetail(ticketId);
  loadDashboard();
}

async function openCreateModal() {
  document.getElementById('createModal').classList.add('active');
}

async function createTicket() {
  const data = {
    channel: document.getElementById('newChannel').value,
    customer_name: document.getElementById('newCustomer').value,
    customer_id: document.getElementById('newCustomerId').value,
    title: document.getElementById('newTitle').value,
    content: document.getElementById('newContent').value,
  };
  try {
    const ticket = await api('/tickets', { method: 'POST', body: JSON.stringify(data) });
    document.getElementById('createModal').classList.remove('active');
    alert(`工单 #${ticket.id} 创建成功\n分类: ${ticket.major_category} > ${ticket.sub_category}\n状态: ${ticket.status}`);
    loadTickets();
    loadDashboard();
  } catch (e) {
    alert('创建失败: ' + e.message);
  }
}

async function refreshAll() {
  loadDashboard();
  loadTickets();
}

document.getElementById('createModal').addEventListener('click', function(e) {
  if (e.target === this) this.classList.remove('active');
});
document.getElementById('detailModal').addEventListener('click', function(e) {
  if (e.target === this) this.classList.remove('active');
});

refreshAll();
