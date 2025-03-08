var CONV = [];

var PFPCache = {};
async function getPfp(pfpElm, pfp) {
    if (!pfp) {
        pfpElm.firstElementChild.src = '';
        pfpElm.lastElementChild.innerText = '';
        return;
    }
    var displTxt = pfp[0];
    if (pfp.length > 1) {
        displTxt += '\n'+pfp.slice(1).join('\n');
    }
    pfpElm.lastElementChild.innerText = displTxt;
    if (PFPCache[pfp]) {
        if (PFPCache[pfp] !== 'null') {
            pfpElm.firstElementChild.src = PFPCache[pfp];
        }
        return;
    }
    var resp = await fetch('/api/v1/ai/pfp/'+encode(pfp.join(' ')))
        .finally(()=>{PFPCache[pfp] = 'null'});
    json = await resp.json();
    if (json.status === 'error') {
        console.error(json);
        // alert(json.message);
        return;
    }
    pfpElm.firstElementChild.src = json.url;
    PFPCache[pfp] = json.url;
}

function makeMessage(role, content, animate = true, pfp = '') {
    var out = document.createElement('div');
    out.classList.add('out');

    if (role === 'bot') {
        var pfpElm = document.createElement('div');
        pfpElm.classList.add('pfpParent');

        var pfpImg = document.createElement('img');
        pfpImg.classList.add('pfp');
        pfpElm.appendChild(pfpImg);
        
        var pfpTooltip = document.createElement('ui-tooltip');
        pfpElm.appendChild(pfpTooltip);

        getPfp(pfpElm, pfp);
        out.appendChild(pfpElm);
    }

    var container = document.createElement('div');
    container.classList.add('msgcontainer')
    if (role === 'user') {
        container.classList.add('myCont');
    }

    var buttons;
    if (role === 'user') {
        buttons = copyTemplate('MychatButtons');
    } else {
        buttons = copyTemplate('AIchatButtons');
    }

    var inn = document.createElement('div');
    inn.classList.add('in');
    if (role === 'user') {
        out.classList.add('myOut');
        inn.classList.add('myIn');
    } else {
        inn.classList.add('botIn');
    }
    if (animate) {
        inn.classList.add('animateFont');
        setTimeout(function(){
            inn.classList.add('anim');
        }, 1)
    }
    var span = document.createElement('span');
    formatText(span, content)
    inn.appendChild(span);
    container.appendChild(inn);
    container.appendChild(buttons);
    out.appendChild(container);
    document.getElementById('messageBubbles').appendChild(out);
    return out;
}

async function addMessage(role, content, pfp = '') {
    const ID = this.location.pathname.split('/')[2];
    var newConv = CONV;
    newConv.push({
        'role': role,
        'content': content,
        'pfp': pfp
    });

    resp = await fetch('/api/v1/chat/'+ID, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'conv': CONV
        })
    });
    json = await resp.json();
    if (json.status === 'error') {
        console.error(json);
        alert(json.message);
        return;
    }
    CONV = json.data.messages;
    return makeMessage(role, content, pfp=pfp);
}

async function updateLastMessage(newContent, pfp) {
    const ID = this.location.pathname.split('/')[2];
    var newConv = CONV;
    newConv[newConv.length - 1].content = newContent;
    if (newConv[newConv.length - 1].pfp !== pfp) {
        var pfpElm = document.getElementById('messageBubbles').lastElementChild.firstElementChild;
        getPfp(pfpElm, pfp);
    }
    newConv[newConv.length - 1].pfp = pfp;

    resp = await fetch('/api/v1/chat/'+ID, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'conv': newConv
        })
    });
    json = await resp.json();
    if (json.status === 'error') {
        console.error(json);
        alert(json.message);
        return;
    }
    CONV = json.data.messages;
}

var scrlAtBtm = true;
var waitingForScrl = false;
var interruptScrlWait = false;
let userScrolling = false;

function setUserScrolling() {
    userScrolling = true;
    setTimeout(() => (userScrolling = false), 100);
}

function onScrollMsgs() {
    if (!userScrolling) {
        return;
    }
    interruptScrlWait = true;
    if (!waitingForScrl) {
        const container = document.getElementById('messages');
        if (container.scrollHeight - container.scrollTop <= container.clientHeight + 1) {
            scrlAtBtm = true;
            const bottomBtn = document.getElementById('goToBottom');
            bottomBtn.style.display = 'none';
        } else {
            scrlAtBtm = false;
            const bottomBtn = document.getElementById('goToBottom');
            bottomBtn.style.display = 'block';
        }
    }
    updateHei();
}

function updateHei() {
    const cont = document.getElementById('chatContainer');
    var hei = cont.offsetHeight + 17*2;
    const bottomCont = document.getElementById('goToBottomContainer');
    bottomCont.style.height = `calc(3em + ${hei}px)`
}

function scrollMsgs() {
    const scrollable = document.getElementById('messages');
    scrollable.scrollTo({ top: scrollable.scrollHeight, behavior: 'smooth' });
    waitForScrollEnd(scrollable);
}
function waitForScrollEnd(container, wait = false) {
    interruptScrlWait = false;
    if (wait) {
        waitingForScrl = true;
    }
    const checkIfAtBottom = () => {
        if (interruptScrlWait) {
            if (wait) {
                scrollable.scrollTo({ top: scrollable.scrollHeight, behavior: 'smooth' });
            } else {
                return;
            }
        }
        if (container.scrollTop + container.clientHeight >= container.scrollHeight - 1) {
            container.scrollTop = container.scrollHeight;
            const bottomBtn = document.getElementById('goToBottom');
            bottomBtn.style.display = 'none';
            scrlAtBtm = true;
            waitingForScrl = false;
        } else {
            requestAnimationFrame(checkIfAtBottom);
        }
    };
    requestAnimationFrame(checkIfAtBottom);
}

async function initAI() {
    disableInp();
    var msg = makeMessage('bot', '');
    var inn = msg.lastElementChild.firstElementChild;
    insertTemplate(inn, 'spinner');
    scrollMsgs(true);
    return msg;
}
async function startAI() {
    await stopAI();
    var msg = await initAI();
    const ID = this.location.pathname.split('/')[2];
    const response = await fetch('/api/v1/ai/start/'+ID, {
        method: 'POST',
        cache: "no-cache",
        headers: {
            'Content-Type': "application/json"
        },
        body: JSON.stringify({
            'conv': CONV, 
            'modelStr': PROVIDER,
            'opts': getOpts()
        })
    });
    streamAI(msg);
}

var lastMsg = "";
var lastpfp = "";
async function streamAI(msg = null) {
    if (!msg) {
        msg = await initAI();
    }
    const ID = this.location.pathname.split('/')[2];
    var pfpElm = msg.firstElementChild;
    var inn = msg.lastElementChild.firstElementChild;
    const response = await fetch('/api/v1/ai/stream/'+ID, {
        cache: "no-cache",
        keepalive: true,
        headers: {
            'Accept': "text/event-stream",
            'Content-Type': "application/json"
        }
    });
    const reader = response.body.getReader();

    var usingSpin = true;

    while (true) {
        var {value, done} = await reader.read();
        var newTxt = new TextDecoder().decode(value);
        var json = `{"data": [${newTxt.slice(0, -1)}]}`;
        try {
            var data = JSON.parse(json).data;
        } catch {
            console.error(newTxt);
            alert('JSON parse error!')
            return;
        }

        var done = false;

        data.forEach(it => {
            if (done) {
                return;
            }
            if (usingSpin && (it.data !== '' || it.done)) {
                usingSpin = false;
                unuseTemplate('spinner');
            }
            getPfp(pfpElm, it.model);
            formatText(inn.firstElementChild, it.data);
            lastMsg = it.data;
            lastpfp = it.model;
            if (it.done) {
                done = true;
                return;
            }
            if (scrlAtBtm) {
                scrollMsgs();
            }
        });
        if (done) {
            await stopAI();
            return;
        }
    }
}

async function stopAI(addLast = true) {
    const ID = window.location.pathname.split('/')[2];
    var fail = false;
    var resp = await fetch('/api/v1/ai/stop/'+ID, {
        method: 'POST',
        cache: "no-cache",
    }).then((response) => {
        if (!response.ok) {
            fail = true;
        }
    });
    if (fail) {
        return;
    }
    if (addLast) {
        CONV.push({role: 'bot', content: lastMsg});
    }
    await updateLastMessage(lastMsg, lastpfp);
    enableInp();
}

function disableInp() {
    const GOBtn = document.getElementById('chatGoBtn');
    GOBtn.firstElementChild.firstElementChild.setAttribute('href', '#stop');
    GOBtn.onclick = stopAI;
    const cont = document.getElementById('chatIn');
    cont.disabled = true;
}
function enableInp() {
    const GOBtn = document.getElementById('chatGoBtn');
    GOBtn.firstElementChild.firstElementChild.setAttribute('href', '#go');
    GOBtn.onclick = onChatGo;
    const cont = document.getElementById('chatIn');
    cont.disabled = false;
}

async function redo(elm, modif = 0) {
    // if (!confirm('You sure you want to redo?')) {
    //     return;
    // }
    await delElm(elm, false, modif);
    await startAI();
}

async function delElm(elm, ask = false, modif = 0) {
    if (ask && !confirm('Are you sure you want to delete this message AND ALL AFTER IT?')) {
        return;
    }
    await stopAI(false);
    const msgs = document.getElementById('messageBubbles');
    for (var i = CONV.length - 1; i >= 0; i--) {
        if (msgs.lastElementChild === elm.parentElement.parentElement.parentElement) {
            if (modif == 0) {
                msgs.removeChild(msgs.lastElementChild);
            }

            const ID = this.location.pathname.split('/')[2];
            resp = await fetch('/api/v1/chat/'+ID, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    'conv': CONV.slice(0, i+modif)
                })
            });
            json = await resp.json();
            if (json.status === 'error') {
                console.error(json);
                alert(json.message);
                return;
            }
            CONV = json.data.messages;
            break;
        }
        msgs.removeChild(msgs.lastElementChild);
    }
}

async function backElm(elm) {
    const msgs = document.getElementById('messageBubbles');
    const parent = elm.parentElement.parentElement.parentElement;
    const idx = Array.prototype.indexOf.call(msgs.children, parent);
    msgs.removeChild(parent);
    const ID = this.location.pathname.split('/')[2];
    const resp = await fetch('/api/v1/chat/'+ID, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'conv': [...CONV.slice(0, idx-1), ...CONV.slice(idx)]
        })
    });
    json = await resp.json();
    if (json.status === 'error') {
        console.error(json);
        alert(json.message);
        return;
    }
    CONV = json.data.messages;
}

function endEdit(elm, idx) {
    elm.innerHTML = '';
    const newSpan = document.createElement('span');
    formatText(newSpan, CONV[idx-1].content);
    elm.appendChild(newSpan);
}
async function editElm(elm, runAft = true) {
    const ID = this.location.pathname.split('/')[2];
    const msg = elm.parentElement.parentElement.parentElement
    const msgs = document.getElementById('messageBubbles');
    const idx = Array.prototype.indexOf.call(msgs.children, msg);
    const msgtxt = elm.parentElement.parentElement.firstElementChild;
    const txtArea = document.createElement('textarea');
    function fixHei(event) {
        txtArea.style.width = "100vw";
        const parentWid = txtArea.parentElement.parentElement.clientWidth;
        txtArea.style.width = "1px";
        txtArea.style.whiteSpace = "pre";
        txtArea.style.width = Math.min(txtArea.scrollWidth, parentWid) + "px";
        txtArea.style.removeProperty('white-space');

        txtArea.style.height = "1px";
        txtArea.style.height = txtArea.scrollHeight + "px";
    }
    txtArea.oninput = fixHei;
    txtArea.value = CONV[idx-1].content;
    msgtxt.innerHTML = '';
    msgtxt.appendChild(txtArea);
    const btnsDiv = document.createElement('div');
    [['yes', async function(){
        var newConv = CONV.slice()
        newConv[idx-1].content = txtArea.value;
        const resp = await fetch('/api/v1/chat/'+ID, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'conv': newConv
            })
        });
        json = await resp.json();
        if (json.status === 'error') {
            console.error(json);
            alert(json.message);
            return;
        }
        CONV = json.data.messages;
        endEdit(msgtxt, idx);
        await delElm(elm, false, 1);
        if (runAft) {
            await startAI();
        }
    }], 
        ['no', function(){ endEdit(msgtxt, idx)} ]].forEach(val => {
        let newBtn = document.createElement('button');
        newBtn.onclick = val[1];
        newBtn.innerHTML = `<svg width="22" height="22"> <use href="#${val[0]}" /> </svg>`;
        newBtn.classList.add('msgEditBtn');
        btnsDiv.appendChild(newBtn);
    })
    msgtxt.appendChild(btnsDiv);
    requestAnimationFrame(()=>{ fixHei() });
}

async function onChatGo() {
    const txt = getChatTxt();
    if (txt === "") {
        return;
    }
    disableInp();
    if (txt.trim()) {
        await addMessage('user', txt);
    }
    setChatTxt("");
    scrollMsgs();
    await startAI();
}

async function loadData() {
    const ID = this.location.pathname.split('/')[2];

    var data;
    if (ID) {
        var resp = await fetch('/api/v1/chat/'+ID);
        data = await resp.json();
        if (data.status === 'error') {
            console.error(data);
            alert(data.message);
            home();
            return;
        }
    } else {
        console.error('No chat ID provided');
        alert('No chat ID provided');
        home();
        return;
    }
    CONV = data.data.messages;
    CONV.forEach(element => {
        makeMessage(element.role, element.content, false, element.pfp);
    });
    const scrollable = document.getElementById('messages');
    scrollable.scrollTop = scrollable.scrollHeight;
    waitForScrollEnd(scrollable);
    if (data.running) {
        disableInp();
        var msg = document.getElementById('messageBubbles').lastElementChild;
        if (msg.classList.contains('myOut')) {
            msg = makeMessage('bot', '');
        }
        if (!data.data.messages[data.data.messages.length-1].content) {
            var inn = msg.lastElementChild.firstElementChild;
            insertTemplate(inn, 'spinner');
        }
        streamAI(msg);
    }
}


function fix_hei() {
    const cont = document.getElementById('chatContainer');
    const hei = cont.offsetHeight + 54;
    document.getElementById('spacer').style.height = hei + 'px';
}

document.addEventListener("DOMContentLoaded", function() {
    const mc = document.getElementById('mainCentre');
    insertTemplate(mc, 'chatContainer');
    unuseTemplate('AIchatButtons');
    unuseTemplate('MychatButtons');

    document.getElementById('chatIn').addEventListener("input", updateHei);

    document.getElementById('messages').addEventListener('wheel', setUserScrolling);
    document.getElementById('messages').addEventListener('touchmove', setUserScrolling);
    document.getElementById('messages').addEventListener('keydown', (event) => {
        if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', 'Space'].includes(event.key)) {
            setUserScrolling();
        }
    });

    document.getElementById('chatIn').addEventListener("input", function() {
        fix_hei();
    });
    
    mc.removeChild(mc.firstElementChild);
    loadData();
    fix_hei();
});
