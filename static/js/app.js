// Application State
let currentView = 'customer';
let activeCustomerId = 'CUST-1001';
let activeTicketId = null;
let currentTicketData = null;
let currentQueueFilter = 'all';
let pieChartInstance = null;
let barChartInstance = null;

// On Page Load
document.addEventListener('DOMContentLoaded', () => {
    loadCustomerProfile(activeCustomerId);
    loadAgentTickets();
    loadKBArticles();
});

// Switch Views
function switchView(viewName) {
    currentView = viewName;

    document.getElementById('view-customer').classList.add('hidden');
    document.getElementById('view-agent').classList.add('hidden');
    document.getElementById('view-analytics').classList.add('hidden');

    const btnCust = document.getElementById('btn-view-customer');
    const btnAgent = document.getElementById('btn-view-agent');
    const btnAnalytics = document.getElementById('btn-view-analytics');

    btnCust.className = 'px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-slate-200';
    btnAgent.className = 'px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-slate-200';
    btnAnalytics.className = 'px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all text-slate-400 hover:text-slate-200';

    if (viewName === 'customer') {
        document.getElementById('view-customer').classList.remove('hidden');
        btnCust.className = 'px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all bg-blue-600 text-white shadow';
    } else if (viewName === 'agent') {
        document.getElementById('view-agent').classList.remove('hidden');
        btnAgent.className = 'px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all bg-blue-600 text-white shadow';
        loadAgentTickets();
    } else if (viewName === 'analytics') {
        document.getElementById('view-analytics').classList.remove('hidden');
        btnAnalytics.className = 'px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all bg-blue-600 text-white shadow';
        loadAnalyticsData();
    }
}

// ==================== CUSTOMER PORTAL LOGIC ====================

function onCustomerSelectChange() {
    const select = document.getElementById('customer-select');
    activeCustomerId = select.value;
    loadCustomerProfile(activeCustomerId);
}

function loadCustomerProfile(customerId) {
    fetch(`/api/customers/${customerId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const customer = data.customer;
                
                const lineBadge = document.getElementById('cust-line-badge');
                const lineText = document.getElementById('cust-line-status-text');
                
                if (customer.line_status === 'Fault Detected') {
                    lineBadge.className = 'flex items-center gap-2 text-xs px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30';
                    lineText.innerText = `Line Status: Fault Detected (${customer.download_speed_mbps} Mbps)`;
                } else if (customer.line_status === 'Degraded') {
                    lineBadge.className = 'flex items-center gap-2 text-xs px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30';
                    lineText.innerText = `Line Status: Degraded (${customer.download_speed_mbps} Mbps)`;
                } else {
                    lineBadge.className = 'flex items-center gap-2 text-xs px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30';
                    lineText.innerText = `Line Status: Online (${customer.download_speed_mbps} Mbps)`;
                }

                if (customer.recent_tickets && customer.recent_tickets.length > 0) {
                    activeTicketId = customer.recent_tickets[0].ticket_id;
                    loadCustomerChatHistory(activeTicketId);
                } else {
                    activeTicketId = null;
                    renderCustomerWelcome(customer);
                }
            }
        });
}

function renderCustomerWelcome(customer) {
    const box = document.getElementById('customer-chat-box');
    box.innerHTML = `
        <div class="flex items-start gap-3 max-w-2xl">
            <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 rounded-2xl text-xs space-y-2 text-slate-200">
                <p class="font-bold text-blue-400">Welcome to ApexConnect Support Assistant!</p>
                <p>Hello ${customer.name}, I am your automated broadband & mobile assistant. I have access to your active plan (<strong>${customer.plan_name}</strong>) and live line diagnostics.</p>
                <p>How can I assist you today? You can choose a suggested question below or type your issue.</p>
            </div>
        </div>
    `;
}

function loadCustomerChatHistory(ticketId) {
    fetch(`/api/tickets/${ticketId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderCustomerMessages(data.ticket.messages);
            }
        });
}

function renderCustomerMessages(messages) {
    const box = document.getElementById('customer-chat-box');
    box.innerHTML = '';

    messages.forEach(msg => {
        const isCustomer = msg.sender === 'customer';
        const msgDiv = document.createElement('div');
        msgDiv.className = isCustomer ? 'flex items-start justify-end gap-3' : 'flex items-start gap-3 max-w-3xl';

        let citationsHTML = '';
        if (msg.citations && msg.citations.length > 0) {
            citationsHTML = `<div class="mt-2.5 flex flex-wrap gap-1.5">${msg.citations.map(c => `<span class="citation-tag"><i class="fa-solid fa-book-bookmark"></i> ${c}</span>`).join('')}</div>`;
        }

        let approvalBadge = '';
        if (msg.sender === 'assistant' && msg.approved_by_agent) {
            approvalBadge = `<div class="mt-2 text-[10px] text-emerald-400 font-semibold flex items-center gap-1"><i class="fa-solid fa-circle-check"></i> Approved & Verified by Support Agent</div>`;
        }

        if (isCustomer) {
            msgDiv.innerHTML = `
                <div class="bg-blue-600 text-white p-4 rounded-2xl text-xs max-w-lg shadow-md leading-relaxed">
                    ${msg.content}
                </div>
                <div class="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 text-xs font-bold shrink-0">
                    <i class="fa-solid fa-user"></i>
                </div>
            `;
        } else {
            msgDiv.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold shrink-0 shadow-md">
                    <i class="fa-solid fa-robot"></i>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-4 rounded-2xl text-xs space-y-2 text-slate-200 shadow-md leading-relaxed">
                    <div class="font-bold text-blue-400 flex items-center justify-between">
                        <span>ApexConnect Assistant</span>
                        <span class="text-[10px] text-slate-500 font-normal">${new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                    <div>${formatMessageContent(msg.content)}</div>
                    ${citationsHTML}
                    ${approvalBadge}
                </div>
            `;
        }
        box.appendChild(msgDiv);
    });

    box.scrollTop = box.scrollHeight;
}

function formatMessageContent(text) {
    return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

function sendQuickMessage(text) {
    document.getElementById('customer-input').value = text;
    handleCustomerSubmit(new Event('submit'));
}

function handleCustomerSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('customer-input');
    const content = input.value.trim();
    if (!content) return;

    input.value = '';

    if (!activeTicketId) {
        fetch('/api/tickets', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                customer_id: activeCustomerId,
                subject: content.substring(0, 40) + '...',
                category: 'Broadband',
                message: content
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                activeTicketId = data.ticket_id;
                loadCustomerChatHistory(activeTicketId);
                loadAgentTickets();
            }
        });
    } else {
        fetch(`/api/tickets/${activeTicketId}/messages`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                sender: 'customer',
                content: content
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                loadCustomerChatHistory(activeTicketId);
                loadAgentTickets();
            }
        });
    }
}

// ==================== DIAGNOSTICS MODAL ====================

function openDiagnosticsModal() {
    document.getElementById('diagnostics-modal').classList.remove('hidden');
    fetch('/api/diagnostics/run', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({customer_id: activeCustomerId})
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const d = data.diagnostics;
            document.getElementById('diag-status').innerText = d.line_status;
            document.getElementById('diag-ping').innerText = `${d.ping_ms} ms`;
            document.getElementById('diag-down').innerText = `${d.download_mbps} Mbps`;
            document.getElementById('diag-up').innerText = `${d.upload_mbps} Mbps`;
            document.getElementById('diag-snr').innerText = `${d.signal_noise_ratio_db} dB`;
            document.getElementById('diag-rec').innerText = d.recommendation;
        }
    });
}

function closeDiagnosticsModal() {
    document.getElementById('diagnostics-modal').classList.add('hidden');
}


// ==================== AGENT RESOLUTION DESK LOGIC ====================

function loadAgentTickets() {
    fetch(`/api/tickets?status=${currentQueueFilter}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderTicketList(data.tickets);
            }
        });
}

function filterQueue(filterType) {
    currentQueueFilter = filterType;

    ['all', 'routine', 'missing', 'escalated'].forEach(f => {
        const btn = document.getElementById(`filter-${f}`);
        if (btn) btn.className = 'py-1.5 rounded text-slate-400 hover:bg-slate-800';
    });

    const activeBtn = document.getElementById(`filter-${filterType === 'routine_draft' ? 'routine' : filterType === 'missing_info' ? 'missing' : filterType}`);
    if (activeBtn) activeBtn.className = 'py-1.5 rounded bg-slate-800 text-blue-400 font-bold';

    loadAgentTickets();
}

function renderTicketList(tickets) {
    const container = document.getElementById('ticket-list-container');
    container.innerHTML = '';

    if (tickets.length === 0) {
        container.innerHTML = `<div class="text-center py-8 text-xs text-slate-500">No tickets found in this filter.</div>`;
        return;
    }

    tickets.forEach(ticket => {
        const item = document.createElement('div');
        const isSelected = ticket.ticket_id === activeTicketId;

        let badgeClass = 'bg-blue-500/20 text-blue-400 border-blue-500/30';
        let badgeText = 'Routine Draft';

        if (ticket.status === 'escalated') {
            badgeClass = 'bg-amber-500/20 text-amber-400 border-amber-500/30';
            badgeText = 'Escalated Handover';
        } else if (ticket.status === 'missing_info') {
            badgeClass = 'bg-purple-500/20 text-purple-400 border-purple-500/30';
            badgeText = 'Needs Info';
        } else if (ticket.status === 'resolved') {
            badgeClass = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
            badgeText = 'Resolved';
        }

        item.className = `p-3 rounded-xl border transition-all cursor-pointer ${
            isSelected
                ? 'bg-slate-800 border-blue-500/60 shadow-md'
                : 'bg-slate-950 border-slate-800/80 hover:bg-slate-900 hover:border-slate-700'
        }`;

        item.onclick = () => selectAgentTicket(ticket.ticket_id);

        item.innerHTML = `
            <div class="flex items-center justify-between mb-1">
                <span class="font-bold text-xs text-slate-200">${ticket.ticket_id}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-semibold border ${badgeClass}">${badgeText}</span>
            </div>
            <p class="font-medium text-xs text-slate-300 truncate">${ticket.subject}</p>
            <div class="flex items-center justify-between mt-2 text-[10px] text-slate-500">
                <span>${ticket.customer_name}</span>
                <span class="font-mono text-slate-400">${new Date(ticket.updated_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
            </div>
        `;

        container.appendChild(item);
    });
}

function selectAgentTicket(ticketId) {
    activeTicketId = ticketId;
    loadAgentTickets();

    fetch(`/api/tickets/${ticketId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                currentTicketData = data.ticket;
                renderAgentWorkspace(data.ticket);
                renderCustomer360(data.ticket);
            }
        });
}

function renderAgentWorkspace(ticket) {
    document.getElementById('agent-workspace-empty').classList.add('hidden');
    document.getElementById('agent-workspace-content').classList.remove('hidden');

    document.getElementById('agent-ticket-subject').innerText = ticket.subject;
    document.getElementById('agent-ticket-id').innerText = ticket.ticket_id;
    document.getElementById('agent-ticket-customer').innerText = ticket.customer_name;
    document.getElementById('agent-ticket-category').innerText = ticket.category;

    const badge = document.getElementById('agent-ticket-status-badge');
    const exportBtn = document.getElementById('btn-export-handover');

    if (ticket.status === 'escalated') {
        badge.className = 'px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30';
        badge.innerText = 'Escalated Handover';
        exportBtn.classList.remove('hidden');
    } else if (ticket.status === 'routine_draft') {
        badge.className = 'px-3 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30';
        badge.innerText = 'Routine Draft Ready';
        exportBtn.classList.add('hidden');
    } else if (ticket.status === 'missing_info') {
        badge.className = 'px-3 py-1 rounded-full text-xs font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30';
        badge.innerText = 'Needs Information';
        exportBtn.classList.add('hidden');
    } else {
        badge.className = 'px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
        badge.innerText = 'Resolved';
        exportBtn.classList.add('hidden');
    }

    const handoverCard = document.getElementById('handover-card-container');
    if (ticket.status === 'escalated' && ticket.handover) {
        handoverCard.classList.remove('hidden');
        document.getElementById('handover-issue-text').innerText = ticket.handover.issue_summary;

        const facts = ticket.handover.established_facts;
        const factsList = document.getElementById('handover-facts-list');
        factsList.innerHTML = `
            <li>• <strong>Account ID</strong>: ${facts.account_id} (${facts.account_tier})</li>
            <li>• <strong>Plan</strong>: ${facts.service_plan}</li>
            <li>• <strong>Billing Status</strong>: ${facts.billing_status}</li>
            <li>• <strong>Line Telemetry</strong>: ${facts.line_telemetry}</li>
        `;

        const tried = ticket.handover.tried_solutions;
        const triedList = document.getElementById('handover-tried-list');
        triedList.innerHTML = tried.attempted_steps.map(s => `<li>• ${s}</li>`).join('');

        document.getElementById('handover-action-text').innerText = ticket.handover.recommended_action;
    } else {
        handoverCard.classList.add('hidden');
    }

    const lastAssistantMsg = [...ticket.messages].reverse().find(m => m.sender === 'assistant');
    if (lastAssistantMsg) {
        document.getElementById('agent-draft-textarea').value = lastAssistantMsg.content;
        const tagsContainer = document.getElementById('draft-citations-tags');
        if (lastAssistantMsg.citations && lastAssistantMsg.citations.length > 0) {
            tagsContainer.innerHTML = lastAssistantMsg.citations.map(c => `<span class="citation-tag"><i class="fa-solid fa-bookmark"></i> ${c}</span>`).join('');
        } else {
            tagsContainer.innerHTML = '<span class="text-slate-500">No explicit citations</span>';
        }
    } else {
        document.getElementById('agent-draft-textarea').value = 'No automated draft available.';
    }

    const logBox = document.getElementById('agent-chat-log');
    logBox.innerHTML = ticket.messages.map(m => `
        <div class="p-2.5 rounded-lg text-xs ${m.sender === 'customer' ? 'bg-blue-950/40 border border-blue-800/40 text-blue-200' : 'bg-slate-900 border border-slate-800 text-slate-300'}">
            <div class="flex justify-between font-bold mb-1 ${m.sender === 'customer' ? 'text-blue-400' : 'text-indigo-400'}">
                <span class="capitalize">${m.sender}</span>
                <span class="text-[10px] text-slate-500 font-normal">${new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
            </div>
            <div>${formatMessageContent(m.content)}</div>
        </div>
    `).join('');

    logBox.scrollTop = logBox.scrollHeight;
}

function renderCustomer360(ticket) {
    document.getElementById('c360-name').innerText = ticket.customer_name;
    document.getElementById('c360-tier').innerText = `${ticket.account_tier} Account`;
    document.getElementById('c360-plan').innerText = ticket.plan_name;
    document.getElementById('c360-billing').innerText = ticket.billing_status;
    document.getElementById('c360-hardware').innerText = ticket.modem_router_id || 'SIM-5G-ACTIVE';
    document.getElementById('c360-speeds').innerText = `${ticket.download_speed_mbps || '--'} / ${ticket.upload_speed_mbps || '--'} Mbps`;
    document.getElementById('c360-latency').innerText = ticket.line_status === 'Fault Detected' ? '145 ms (High)' : '8 ms';
}

function approveCurrentDraft() {
    if (!activeTicketId) return;

    fetch(`/api/tickets/${activeTicketId}/approve`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert('Draft approved and dispatched to customer!');
            selectAgentTicket(activeTicketId);
        }
    });
}

function resolveCurrentTicket() {
    if (!activeTicketId) return;
    approveCurrentDraft();
}

function exportHandoverSummary() {
    if (!activeTicketId) return;
    fetch(`/api/tickets/${activeTicketId}/export`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const jsonStr = JSON.stringify(data.export, null, 2);
                const blob = new Blob([jsonStr], {type: 'application/json'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Handover_${activeTicketId}.json`;
                a.click();
            }
        });
}

function handleAgentReply(e) {
    e.preventDefault();
    const input = document.getElementById('agent-reply-input');
    const content = input.value.trim();
    if (!content || !activeTicketId) return;

    input.value = '';

    fetch(`/api/tickets/${activeTicketId}/messages`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            sender: 'agent',
            content: content
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            selectAgentTicket(activeTicketId);
        }
    });
}

function runTelemetryCheckAgent() {
    if (!currentTicketData) return;
    fetch('/api/diagnostics/run', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({customer_id: currentTicketData.customer_id})
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(`Line Diagnostics Result:\nStatus: ${data.diagnostics.line_status}\nPing: ${data.diagnostics.ping_ms} ms\nRecommendation: ${data.diagnostics.recommendation}`);
        }
    });
}

// ==================== KB MANAGEMENT LOGIC ====================

function loadKBArticles() {
    fetch('/api/kb')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderKBArticles(data.articles);
            }
        });
}

function searchKBArticles() {
    const query = document.getElementById('kb-search-input').value;
    fetch(`/api/kb?query=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderKBArticles(data.articles);
            }
        });
}

function renderKBArticles(articles) {
    const list = document.getElementById('kb-articles-list');
    list.innerHTML = articles.map(art => `
        <div class="p-2.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1 text-xs hover:border-slate-700 transition-colors">
            <div class="flex items-center justify-between">
                <span class="font-bold text-slate-200 truncate">${art.title}</span>
                <span class="citation-tag">${art.citation_tag}</span>
            </div>
            <p class="text-[11px] text-slate-400 line-clamp-2">${art.content}</p>
        </div>
    `).join('');
}

function openAddKBModal() {
    document.getElementById('kb-modal').classList.remove('hidden');
}

function closeAddKBModal() {
    document.getElementById('kb-modal').classList.add('hidden');
}

function handleAddKBSubmit(e) {
    e.preventDefault();
    const article = {
        article_id: document.getElementById('kb-input-id').value,
        title: document.getElementById('kb-input-title').value,
        category: 'Broadband',
        keywords: document.getElementById('kb-input-keywords').value,
        content: document.getElementById('kb-input-content').value,
        resolution_template: document.getElementById('kb-input-template').value
    };

    fetch('/api/kb', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(article)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            closeAddKBModal();
            loadKBArticles();
            alert('Knowledge Article Added Successfully!');
        }
    });
}

// ==================== ANALYTICS & CHARTS LOGIC ====================

function loadAnalyticsData() {
    fetch('/api/analytics')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const m = data.metrics;
                document.getElementById('metric-deflection').innerText = `${m.deflection_rate_pct}%`;
                document.getElementById('metric-total-tickets').innerText = m.total_tickets;
                document.getElementById('metric-time-saved').innerText = `${m.avg_time_saved_mins}m`;

                renderAnalyticsCharts(m);
            }
        });
}

function renderAnalyticsCharts(metrics) {
    // Pie Chart
    const pieCtx = document.getElementById('chart-queue-pie').getContext('2d');
    if (pieChartInstance) pieChartInstance.destroy();

    pieChartInstance = new Chart(pieCtx, {
        type: 'doughnut',
        data: {
            labels: ['Routine Drafts', 'Needs Info', 'Escalated Handover', 'Resolved'],
            datasets: [{
                data: [metrics.routine_draft_count, metrics.missing_info_count, metrics.escalated_count, metrics.resolved_count],
                backgroundColor: ['#3b82f6', '#a855f7', '#f59e0b', '#10b981']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8' } }
            }
        }
    });

    // Bar Chart
    const barCtx = document.getElementById('chart-volume-bar').getContext('2d');
    if (barChartInstance) barChartInstance.destroy();

    barChartInstance = new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Today'],
            datasets: [{
                label: 'Resolved Routine Cases',
                data: [12, 19, 15, 25, 22, 18, metrics.routine_draft_count + metrics.resolved_count],
                backgroundColor: '#3b82f6'
            }, {
                label: 'Human Escalation Handovers',
                data: [3, 5, 2, 6, 4, 3, metrics.escalated_count],
                backgroundColor: '#f59e0b'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } }
            },
            plugins: {
                legend: { labels: { color: '#94a3b8' } }
            }
        }
    });
}
