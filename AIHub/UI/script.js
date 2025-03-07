var PROVIDER = 'best';
function encode(str) {
    return encodeURIComponent(str.replace('/', '\\'));
}
function copyCodeBlock(elm) {
    navigator.clipboard.writeText(elm.parentElement.parentElement.lastElementChild.innerText.replaceAll(/\s(?<![\n\t\r\f\v ])/g, ' '));
    let origTxt = elm.innerText;
    elm.innerText = '✔ Copied!';
    setTimeout(()=>{
        elm.innerText = origTxt;
        elm.blur();
    }, 1000)
}
function runHTML(elm) {
    const container = document.getElementById('popupContent');
    const shadow = container.attachShadow({ mode: 'closed' });
    const html = document.createElement('html');
    html.innerHTML = elm.parentElement.parentElement.lastElementChild.innerText.replaceAll(/\s(?<![\n\t\r\f\v ])/g, ' ');
    shadow.appendChild(html);
    document.getElementById('popup').classList.add('overlay-open');
}
function formatText(elm, str) {
    var safeText = str
        .replaceAll(/&/gm, "&amp;")
        .replaceAll(/</gm, "&lt;")
        .replaceAll(/>/gm, "&gt;")
        .replaceAll(/"/gm, "&quot;")
        .replaceAll(/'/gm, "&#039;");
    
    if (safeText.startsWith('&lt;think&gt;')) {
        let thoughtsHeader = '<summary><span class="txt-outline">💭</span>  Thoughts</summary>';
        if (safeText.match(/^&lt;[\/\\]think&gt;$/gm) !== null) {
            safeText = safeText.replace(/^&lt;think&gt;\n((?:.|\n)+)\n&lt;[\/\\]think&gt;\n?/g, `<details class="thoughts" open>${thoughtsHeader}$1</details>`);
        } else {
            safeText = `<details class="thoughts" open>${thoughtsHeader}${safeText.slice('&lt;think&gt;\n'.length)}</details>`
        }
    }
    
    var blocks = [];
    // TODO: Backslashes
    safeText.split(/^\s*```/gm).forEach((val, idx)=>{
        var newVal;
        if (idx % 2 == 0) {
            newVal = val
                .replaceAll(/^(\s*)&gt; (.+)$/gm, (_, spaces, content) => {
                    let margin = Math.floor(spaces.replace('\t', '    ').length / 2)*2;
                    return `<span class="quote" style="margin-left: ${margin}em;">${content}</span>`
                })
                .replaceAll(/^(?:(?:\|.*)+\|\n){2,}/gm,
                (match) => {
                    var spl = match.split('\n');
                    // let weighting = spl[1].split('|'); // TODO
                    var end = '<tr>';
                    spl[0].split('|').forEach(val=>{
                        if (val) {
                            end += `<td class="table-top"><b>${val}</b></td>`;
                        }
                    });
                    end += '</tr>';
                    spl.slice(2).forEach(row=>{
                        if (row) {
                            end += '<tr>';
                            row.split('|').forEach(val=>{
                                if (val) {
                                    end += `<td>${val}</td>`;
                                }
                            });
                            end += '</tr>';
                        }
                    });

                    return `<table class="format-table">${end}</table>`
                })
                .replaceAll(/^(\s*)[-*] (.*)/gm, (_, spaces, content) => {
                    let margin = Math.floor(spaces.replace('\t', '    ').length / 2)*2;
                    return `<ul><li style="margin-left: ${margin}em;">${content}</li></ul>`;
                })
                .replaceAll(/<\/ul>\s*<ul>/g, '')
                .replaceAll(/^(\s*)(\d+)[.) ](.*)/gm, (_, spaces, number, content) => {
                    let margin = Math.floor(spaces.replace('\t', '    ').length / 2)*2;
                    return `<ol><li value="${number}" style="margin-left: ${margin}em;">${content}</li></ol>`;
                })
                .replaceAll(/<\/ol>\s*<ol>/g, '')
                
                .replaceAll(/!\[(.*)\]\((.*)\)/g, '<img class="format-img" href="$2" alt="$1">')
                .replaceAll(/\[(.*)\]\((.*)\)/g, '<a href="$2">$1</a>')

                .replaceAll(/^# ([^\n]*)$/gm, '<h1>$1</h1>')
                .replaceAll(/^## ([^\n]*)$/gm, '<h2>$1</h2>')
                .replaceAll(/^### ([^\n]*)$/gm, '<h3>$1</h3>')
                .replaceAll(/^#### ([^\n]*)$/gm, '<h4>$1</h4>')
                .replaceAll(/^##### ([^\n]*)$/gm, '<h5>$1</h5>')
                .replaceAll(/^###### ([^\n]*)$/gm, '<h6>$1</h6>')
                .replaceAll(/`([^`\n]+)`/g, '<span class="code-inline">$1</span>')

                .replaceAll(/^[*\-_]{3}$/gm, '<hr>')

                .replaceAll(/>\n+/gm, '>')
                .replaceAll('\n</div>', '</div>')

                .replaceAll(/[*_]{2}((?=[^*_])[^\n<]+?(?<=[^*_]))[*_]{2}/g,'<b>$1</b>')
                .replaceAll(/[*_]((?=[^*_])(?:[^\n<]|(?:<\/?b>))+?(?<=[^*_]))[*_]/g, '<i>$1</i>')
        } else {
            const newlineIndex = val.indexOf('\n');
            let language = '';
            let code = val;
            
            if (newlineIndex !== -1) {
                language = val.slice(0, newlineIndex).trim();
                code = val.slice(newlineIndex + 1);
            }
            
            var btn = '';
            if (!language) {
                language = 'plain'
            } else {
                const lang = language.toLowerCase().trim();
                if (lang === "html") {
                    btn = '<button onclick="runHTML(this)">💻Run code</button>'
                }
            }

            newVal = `<div class="code-block"><div class="codetop"><span class="codelang">${language}</span>${btn}<button onclick="copyCodeBlock(this)">📋️ Copy</button></div><div class="code-${language} code-block-txt">${code}</div></div><br>`;
        }
        blocks.push(
            newVal
                .replaceAll('\t', '&emsp;')
                .replaceAll(/^ +/gm, match => '&nbsp;'.repeat(match.length))
                .replaceAll('\n\n', '<br>')
                .replaceAll('\n', '<br>')
        )
    })

    elm.innerHTML = blocks.join('');
}
function getOpts() {
    var opts = {};
    document.getElementById('PromptSetts').childNodes.forEach(it => {
        var id = it.id;
        if (!id) {
            if (it.classList.contains('inpParent')) {
                it = it.lastElementChild;
                id = it.id;
            }
            if (!id) {
                return;
            }
        }
        var val;
        switch (it.getAttribute('type')) {
            case 'checkbox':
                val = it.value === 'on';
                break;
            case 'number':
                val = parseFloat(it.value);
                break;
            case 'choice':
                var txt = null;
                it.childNodes.forEach(node=>{
                    if (node.value === it.value) {
                        txt = node.innerText;
                    }
                });
                val = [parseInt(it.value), txt];
                break;
            default:
                return;
        }
        opts[id] = val;
    });
    return opts;
}
function init() {
    const Chat = document.getElementById("chatIn");
    Chat.addEventListener("paste", function(e) {
        e.preventDefault();
        const pasted = e.clipboardData.getData("text/plain");
        if (!pasted) {
            return;
        }
        if (Chat.classList.contains("placeholder")) {
            Chat.textContent = "";
            Chat.classList.remove("placeholder");
        }
        const sel = window.getSelection();
        if (sel.rangeCount > 0) {
            let range = sel.getRangeAt(0);
            // Delete any selected content
            range.deleteContents();
            // Create a text node with the pasted content
            const textNode = document.createTextNode(pasted);
            // Insert the text node at the caret position
            range.insertNode(textNode);
            // Move the caret immediately after the inserted text node
            range.setStartAfter(textNode);
            range.collapse(true);
            sel.removeAllRanges();
            sel.addRange(range);
        } else {
            // Fallback: append the text if no caret is found
            setChatTxt(getChatTxt() + pasted);
        }
        if (getChatTxt() === "") {
            Chat.classList.add("placeholder");
        }
        if (Chat.classList.contains("placeholder")) {
            Chat.innerText = Chat.getAttribute("data-placeholder");
        }
    });
    
    var OSL = document.getElementById("openSideLeft");
    OSL.onclick = function() {
        var sideLeft = document.getElementById("sideLeft");
        sideLeft.classList.remove("sideAnim");
        if (OSL.classList.contains("visible")) {
            OSL.classList.replace("visible", "hidden");
        }
        else {
            OSL.classList.add("hidden");
        }
        localStorage.setItem('LeftSideOpen', true);
    }

    function CloseLeft() {
        var sideLeft = document.getElementById("sideLeft");
        sideLeft.classList.add("sideAnim");
        if (OSL.classList.contains("hidden")) {
            OSL.classList.replace("hidden", "visible");
        }
        else {
            OSL.classList.add("visible");
        }
        localStorage.setItem('LeftSideOpen', false);
    }

    document.getElementById("closeSideLeft").onclick = CloseLeft;
    
    if (localStorage.getItem('LeftSideOpen') === 'false') {
        CloseLeft();
        requestAnimationFrame(function(){
            sideLeft.style.transition = 'none';
            // Force reflow
            void sideLeft.offsetWidth;
            sideLeft.style.transition = '';
            sideLeft.classList.add('sidebarTrans');
        });
    } else {
        document.getElementById('sideLeft').classList.add('sidebarTrans');
    }

    var OSR = document.getElementById("openSideRight");
    OSR.onclick = function() {
        var sideRight = document.getElementById("sideRight");
        sideRight.classList.remove("sideAnim");
        if (OSR.classList.contains("visible")) {
            OSR.classList.replace("visible", "hidden");
        }
        else {
            OSR.classList.add("hidden");
        }
        localStorage.setItem('RightSideOpen', true);
    }

    function CloseRight() {
        var sideRight = document.getElementById("sideRight");
        sideRight.classList.add("sideAnim");
        if (OSR.classList.contains("hidden")) {
            OSR.classList.replace("hidden", "visible");
        }
        else {
            OSR.classList.add("visible");
        }
        localStorage.setItem('RightSideOpen', false);
    }
    document.getElementById("closeSideRight").onclick = CloseRight;

    if (!localStorage.getItem('RightSideOpen') || localStorage.getItem('RightSideOpen') === 'false') {
        CloseRight();
        requestAnimationFrame(function(){
            sideRight.style.transition = 'none';
            // Force reflow
            void sideRight.offsetWidth;
            sideRight.style.transition = '';
            sideRight.classList.add('sidebarTrans');
        });
    } else {
        document.getElementById('sideRight').classList.add('sidebarTrans');
    }

    if (!('/'.includes(window.location.pathname))) {
        document.getElementById('newChat').classList.replace('slightlyHidden', 'visible');
    }

    const editable = document.getElementById("chatIn");
    editable.addEventListener("mousedown", function(event) {
        if (this.classList.contains("placeholder")) {
            event.preventDefault(); // Prevent default caret placement
            const range = document.createRange();
            range.setStart(this, 0);
            range.collapse(true);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        }
    });

    function isPrintableKey(event) {
        return event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey;
    }
    editable.addEventListener("keydown", function() {
        if (this.classList.contains("placeholder")) {
            if (!isPrintableKey(event)) {
                return;
            }
            this.textContent = "";
            this.classList.remove("placeholder");
        }
    });
    editable.addEventListener("input", function() {
        if (this.textContent === "") {
            this.classList.add("placeholder");
        }
        if (this.classList.contains("placeholder")) {
            this.innerText = this.getAttribute("data-placeholder");
        }
    });
    editable.innerText = editable.getAttribute("data-placeholder");

    parent = document.getElementById('chatBorder');
    parent.onclick = () => {
        const firstChild = parent.firstElementChild;
        if (firstChild) {
            firstChild.focus();
        }
    };

    function UpdateText() {
        fetch('/api/v1/ai/info/'+encode(PROVIDER))
            .then(resp => resp.json())
            .then(data => {
                formatText(document.getElementById('AIText'), data.data);
            });
    }

    fetch('/api/v1/ai/get')
        .then(resp => resp.json())
        .then(data => {
            const modeSels = document.getElementById('AIDropdowns');
            function hierachyBranch(branch, befores, prov, restoreBranch=null) {
                var select = document.createElement('select');
                select.onchange = function() {
                    var times = modeSels.children.length-befores-1
                    for (i = 0;i < times; i++) {
                        modeSels.removeChild(modeSels.children[befores+1]);
                    }
                    if (!isNaN(this.value) && !isNaN(parseFloat(this.value))) {
                        const val = branch[this.value];
                        if (val[0].includes('<*sep*>')) {
                            PROVIDER = prov+val[0].split('<*sep*>')[1]+':';
                        } else {
                            PROVIDER = prov+val[0]+':';
                        }
                        hierachyBranch(val[1], befores+1, PROVIDER);
                        PROVIDER += 'best';
                    } else {
                        PROVIDER = prov+this.value;
                    }
                    loadOpts();
                    UpdateText();
                    localStorage.setItem('hierachy', PROVIDER);
                    this.blur();
                };
                ['best', 'random'].forEach(val => {
                    var optionA = document.createElement('option');
                    optionA.value = val;
                    optionA.textContent = val;
                    select.appendChild(optionA);
                });
                
                var group = document.createElement('optgroup');
                group.label = 'Provider choices:';
                branch.forEach((val, idx) => {
                    var option = document.createElement('option');
                    if (Array.isArray(val)) {
                        option.value = idx;
                        if (val[0].includes('<*sep*>')) {
                            option.textContent = val[0].split('<*sep*>')[0] + ' ...';
                        } else {
                            option.textContent = val[0] + ' ...';
                        }
                    } else {
                        if (val.includes('<*sep*>')) {
                            let sep = val.split('<*sep*>');
                            option.value = sep[1];
                            option.textContent = sep[0];
                        } else {
                            option.value = val;
                            option.textContent = val;
                        }
                    }
                    group.appendChild(option);
                });
                select.appendChild(group);
                modeSels.appendChild(select);

                if (restoreBranch) {
                    var colIdx = restoreBranch.indexOf(':');
                    if (colIdx !== -1) {
                        let bef = restoreBranch.slice(0, colIdx);
                        let aft = restoreBranch.slice(colIdx+1);
                        let idx = branch.findIndex(val => {
                            if (!Array.isArray(val)) {
                                return false;
                            }
                            if (val[0].includes('<*sep*>')) {
                                return val[0].split('<*sep*>')[1] === bef;
                            } else {
                                return val[0] === bef;
                            }
                            
                        });
                        select.value = idx;
                        hierachyBranch(branch[idx][1], befores+1, prov+bef+':', aft);
                    } else {
                        select.value = restoreBranch;
                    }
                }
            }
            if (localStorage.getItem('hierachy')) {
                PROVIDER = localStorage.getItem('hierachy');
            }
            hierachyBranch(data.data, 0, '', localStorage.getItem('hierachy'));
            loadOpts();
            UpdateText();
        });
}

async function loadOpts() {
    const opts = document.getElementById('PromptSetts');
    const leng = opts.children.length;
    for (i = 0;i < leng;i++) {
        opts.removeChild(opts.firstElementChild);
    }
    resp = await fetch('/api/v1/ai/opts/'+encode(PROVIDER));
    json = await resp.json();
    json.opts.forEach(it => {
        const id = it.id || '';
        switch(it.type) {
            case 'header':
                const header = document.createElement('h4');
                header.id = id;
                header.innerText = it.label;
                opts.appendChild(header);
                break;
            case 'numInp':
                var labelElem = document.createElement('label');
                labelElem.innerText = it.label;
                opts.appendChild(labelElem);
                const numInput = document.createElement('input');
                numInput.id = id;
                numInput.type = 'number';
                numInput.defaultValue = it.default;
                numInput.min = it.min;
                numInput.max = it.max;
                numInput.step = it.step || 1;
                opts.appendChild(numInput);
                break;
            case 'boolInp':
                const boolLabel = document.createElement('div');
                boolLabel.classList.add('boolLabel');
                boolLabel.classList.add('inpParent');
                const label = document.createElement('p');
                label.innerText = it.label;
                boolLabel.appendChild(label);
                const boolInput = document.createElement('input');
                boolInput.id = id;
                boolInput.type = 'checkbox';
                boolInput.checked = it.default;
                boolLabel.appendChild(boolInput);
                opts.appendChild(boolLabel);
                break;
            case 'choiceInp':
                var labelElem = document.createElement('label');
                labelElem.innerText = it.label;
                opts.appendChild(labelElem);
                const choiceInp = document.createElement('select');
                choiceInp.id = id;
                choiceInp.setAttribute('type', 'choice');
                it.choices.forEach((txt, idx) => {
                    var choice = document.createElement('option');
                    choice.value = idx;
                    choice.innerText = txt;
                    choiceInp.appendChild(choice);
                });
                choiceInp.value = it.default;
                opts.appendChild(choiceInp);
                break;
            default:
                console.error(`Unknown type ${it.type}`)
        }
    });
}

function closePopup() {
    document.getElementById('popup').classList.remove('overlay-open');
    var popupC = document.getElementById('popupContent');
    var parent = popupC.parentElement;
    parent.removeChild(popupC);
    var newdiv = document.createElement('div');
    newdiv.id = 'popupContent';
    parent.appendChild(newdiv);
}

function home() {
    if (!('/'.includes(window.location.pathname))) {
        window.location = '/';
    }
}

function getChatTxt() {
    const chatBox = document.getElementById('chatIn');
    if (chatBox.classList.contains('placeholder')) {
        return "";
    }
    return chatBox.innerText;
}
function setChatTxt(txt) {
    const chatBox = document.getElementById('chatIn');
    if (txt === "") {
        chatBox.classList.add('placeholder');
        chatBox.innerText = chatBox.getAttribute("data-placeholder");
    } else {
        chatBox.classList.remove('placeholder');
        chatBox.innerText = txt;
    }
}

var SELECTED = null;
function findConvs() {
    fetch('/api/v1/chat')
        .then(resp => resp.json())
        .then(json => {
            if (json.status === 'error') {
                console.error(json);
                alert(json.message);
                return;
            }
            const data = json.data;
            const parent = document.getElementById('prevChats');
            const len = parent.childNodes.length;
            for (i = 0;i < len;i++) {
                parent.removeChild(parent.firstChild);
            }
            data.forEach(element => {
                var parentDiv = copyTemplate('PrevChatBtn');
                var button = parentDiv.firstElementChild;
                button.onclick = function() {
                    window.location = '/chat/'+element[0];
                }
                button.firstElementChild.innerText = element[1];

                var btn2 = button.lastElementChild;

                btn2.onclick = function(event) {
                    event.stopPropagation();
                    const MP = document.getElementById('morePage');
                    if (MP.parentElement.id !== "defs" && (!MP.contains(event.target)) && parentDiv.contains(MP)) {
                        unuseTemplate('morePage');
                    } else {
                        unuseTemplate('renameInp')
                        insertTemplate(parentDiv, 'morePage');
                        SELECTED = element[0];
                    }
                };

                parent.appendChild(parentDiv);
            });
        });
}
findConvs();

function deleteConv() {
    if (SELECTED === null) { // || !confirm('Are you sure you want to delete this chat?')) {
        return;
    }
    fetch('/api/v1/chat/'+SELECTED, {
        method: 'DELETE'
    })
        .then(resp => resp.json())
        .then(json => {
            if (json.status === 'error') {
                console.error(json);
                alert(json.message);
                return;
            }
            if (window.location.pathname === "/chat/"+SELECTED) {
                window.location.replace('/');
            }
            unuseTemplate('morePage');
            findConvs();
        });
}

function renameConv() {
    const parent = document.getElementById('morePage').parentElement;
    unuseTemplate('morePage');
    const inp = insertTemplate(parent, 'renameInp');
    inp.value = "";
    inp.placeholder = parent.firstElementChild.firstElementChild.innerText;
    inp.focus();
    inp.onblur = function() {
        if (inp.value === "") {
            inp.onblur = function() {};
            unuseTemplate('renameInp');
            return;
        }
        fetch('/api/v1/chat/'+SELECTED, {
            method: 'PUT',
            headers: {
                'Content-Type': "application/json"
            },
            body: JSON.stringify({'name': inp.value})
        })
            .then(resp => resp.json())
            .then(json => {
                if (json.status === 'error') {
                    console.error(json);
                    alert(json.message);
                    return;
                }
                parent.firstElementChild.firstElementChild.innerText = inp.value;
                inp.onblur = function() {};
                unuseTemplate('renameInp');
            });
    }
}

document.addEventListener('click', function(event) {
    if (event.target.closest('.moreBtn')) {
        return;
    }

    document.querySelectorAll('select').forEach(function(select) {
        if (!select.contains(event.target)) {
            select.blur();
        }
    });

    const MP = document.getElementById('morePage');
    if (MP.parentElement.id !== "defs" && (!MP.contains(event.target))) {
        unuseTemplate('morePage');
    }
});

function insertTemplate(obj, id) {
    const templ = document.getElementById(id);
    obj.appendChild(templ);
    return templ;
}

function copyTemplate(id) {
    const newElm = document.getElementById(id).cloneNode(true);
    newElm.removeAttribute('id');
    return newElm;
}

function unuseTemplate(id) {
    var obj = document.getElementById(id);
    const defs = document.getElementById('defs');
    defs.appendChild(obj);
}

function onChatGo() {} // For overriding
