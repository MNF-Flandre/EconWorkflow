/**
 * 编辑增强功能：代码高亮、在线编辑、搜索、自动刷新
 */

// ===== 1. 代码高亮（使用 highlight.js）=====
function initializeCodeHighlight() {
  const codeBlocks = document.querySelectorAll('pre.file-content');
  codeBlocks.forEach(block => {
    // 根据文件名判断语言
    const fileName = document.querySelector('h1')?.textContent || '';
    let language = 'plaintext';
    
    if (fileName.endsWith('.py')) language = 'python';
    else if (fileName.endsWith('.md')) language = 'markdown';
    else if (fileName.endsWith('.json')) language = 'json';
    else if (fileName.endsWith('.toml')) language = 'toml';
    else if (fileName.endsWith('.csv')) language = 'csv';
    
    block.classList.add('hljs', language);
    
    // 异步加载 highlight.js 并应用高亮
    if (window.hljs) {
      window.hljs.highlightElement(block);
    } else {
      loadHighlightJs(() => {
        window.hljs.highlightElement(block);
      });
    }
  });
}

function loadHighlightJs(callback) {
  if (!document.getElementById('hljs-lib')) {
    const link = document.createElement('link');
    link.id = 'hljs-lib';
    link.rel = 'stylesheet';
    link.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-light.min.css';
    document.head.appendChild(link);
    
    const script = document.createElement('script');
    script.id = 'hljs-script';
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js';
    script.onload = callback;
    document.head.appendChild(script);
  } else if (callback) {
    callback();
  }
}

// ===== 2. 在线 Markdown 编辑器 =====
function initializeMarkdownEditor() {
  const editButton = document.getElementById('edit-file-button');
  const editorContainer = document.getElementById('markdown-editor');
  const toolbarPanel = document.getElementById('editor-toolbar');
  
  if (!editButton || !editorContainer) return;
  
  editButton.addEventListener('click', () => {
    toggleMarkdownEditor();
  });
}

function toggleMarkdownEditor() {
  const fileContent = document.querySelector('pre.file-content');
  const editorContainer = document.getElementById('markdown-editor');
  const editButton = document.getElementById('edit-file-button');
  
  if (!editorContainer) return;
  
  const isEditing = editorContainer.classList.contains('editor-active');
  
  if (!isEditing) {
    // 打开编辑器
    const content = fileContent.textContent;
    fileContent.style.display = 'none';
    editorContainer.classList.add('editor-active');
    editorContainer.style.display = 'block';
    editButton.textContent = '关闭编辑';
    editButton.classList.add('editor-mode-active');
    
    // 暂停自动刷新
    window.autoRefreshPaused = true;
    
    // 加载 CodeMirror
    loadCodeMirror(() => {
      initializeCodeMirrorEditor(content);
    });
  } else {
    // 关闭编辑器
    fileContent.style.display = 'block';
    editorContainer.classList.remove('editor-active');
    editorContainer.style.display = 'none';
    editButton.textContent = '编辑文件';
    editButton.classList.remove('editor-mode-active');
    
    // 恢复自动刷新
    window.autoRefreshPaused = false;
  }
}

function loadCodeMirror(callback) {
  if (window.CodeMirror) {
    callback();
    return;
  }
  
  // 加载 CSS（先加载样式表）
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css';
  document.head.appendChild(link);
  
  const themeLink = document.createElement('link');
  themeLink.rel = 'stylesheet';
  themeLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/eclipse.min.css';
  document.head.appendChild(themeLink);
  
  // 加载主库脚本
  const script = document.createElement('script');
  script.src = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js';
  script.onload = () => {
    // 根据文件类型加载对应的mode
    const fileName = document.querySelector('h1')?.textContent || '';
    let modeScripts = [];
    
    if (fileName.endsWith('.json')) {
      modeScripts.push('https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/javascript/javascript.min.js');
    } else if (fileName.endsWith('.toml')) {
      modeScripts.push('https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/properties/properties.min.js');
    } else if (fileName.endsWith('.py')) {
      modeScripts.push('https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/python/python.min.js');
    } else {
      modeScripts.push('https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/markdown/markdown.min.js');
    }
    
    // 加载第一个mode脚本
    if (modeScripts.length > 0) {
      const modeScript = document.createElement('script');
      modeScript.src = modeScripts[0];
      modeScript.onload = callback;
      document.head.appendChild(modeScript);
    } else {
      callback();
    }
  };
  document.head.appendChild(script);
}

let cmEditor = null;
let cmEditorLoaded = false;

function getCodeMirrorMode() {
  const fileName = document.querySelector('h1')?.textContent || '';
  if (fileName.endsWith('.json')) return 'application/json';
  if (fileName.endsWith('.toml')) return 'text/x-toml';
  if (fileName.endsWith('.py')) return 'text/x-python';
  if (fileName.endsWith('.csv')) return 'text/csv';
  return 'text/x-markdown';  // 默认 markdown
}

function initializeCodeMirrorEditor(content) {
  const editorDiv = document.getElementById('codemirror-instance');
  if (!editorDiv) return;
  
  const mode = getCodeMirrorMode();
  
  if (cmEditor) {
    // 如果已存在编辑器，更新内容和 mode
    cmEditor.setOption('mode', mode);
    cmEditor.setValue(content);
  } else if (!cmEditorLoaded) {
    // 第一次创建
    cmEditor = window.CodeMirror(editorDiv, {
      value: content,
      mode: mode,
      theme: 'eclipse',
      lineNumbers: true,
      lineWrapping: true,
      tabSize: 2,
      indentUnit: 2,
      indentWithTabs: false,
      extraKeys: {
        "Ctrl-S": saveMarkdownFile,
        "Cmd-S": saveMarkdownFile,
      }
    });
    cmEditorLoaded = true;
  }
}

function saveMarkdownFile() {
  if (!cmEditor) return;
  
  const filePath = document.querySelector('[data-file-path]')?.getAttribute('data-file-path');
  const content = cmEditor.getValue();
  
  if (!filePath) {
    alert('无法获取文件路径');
    return;
  }
  
  const formData = new FormData();
  formData.append('content', content);
  
  fetch(`/api/save-file/${filePath}`, {
    method: 'POST',
    body: formData,
  })
  .then(response => {
    if (response.ok) {
      alert('文件已保存');
      location.reload();
    } else {
      alert('保存失败');
    }
  })
  .catch(err => {
    alert(`保存出错: ${err.message}`);
  });
}

function cancelMarkdownEdit() {
  const editorContainer = document.getElementById('markdown-editor');
  if (editorContainer) {
    editorContainer.style.display = 'none';
  }
}

// ===== 3. 搜索与过滤 =====
function initializeSearch() {
  const searchInputs = document.querySelectorAll('[data-search-target]');
  searchInputs.forEach(input => {
    // 为每个搜索框绑定其对应的搜索面板
    const searchPanel = input.closest('.search-filter-panel');
    input.addEventListener('keyup', (e) => {
      const targetSelector = input.getAttribute('data-search-target');
      const query = input.value.toLowerCase();
      filterItems(targetSelector, query, searchPanel);
    });
  });
}

function filterItems(selector, query, statsContainer = null) {
  const items = document.querySelectorAll(selector);
  let visibleCount = 0;
  let totalCount = 0;
  
  items.forEach(item => {
    totalCount++;
    const text = item.textContent.toLowerCase();
    const matches = text.includes(query);
    
    if (matches) {
      item.classList.remove('search-hidden');
      visibleCount++;
    } else {
      item.classList.add('search-hidden');
    }
  });
  
  // 显示搜索结果统计（只更新指定容器的统计）
  if (statsContainer) {
    const statsElement = statsContainer.querySelector('[data-search-stats]');
    if (statsElement && query.length > 0) {
      statsElement.textContent = `匹配 ${visibleCount} / ${totalCount} 项`;
    } else if (statsElement) {
      statsElement.textContent = '';
    }
  }
}

// ===== 4. 自动刷新 =====
function initializeAutoRefresh() {
  const refreshConfig = document.querySelector('[data-auto-refresh]');
  if (!refreshConfig) return;
  
  const interval = parseInt(refreshConfig.getAttribute('data-refresh-interval') || '30000', 10);
  const projectSlug = document.querySelector('[data-project-slug]')?.getAttribute('data-project-slug');
  
  if (!projectSlug) return;
  
  setInterval(() => {
    refreshProjectContext(projectSlug);
  }, interval);
}

function refreshProjectContext(slug) {
  // 如果用户在编辑文件，暂停刷新
  if (window.autoRefreshPaused) {
    return;
  }
  
  fetch(`/api/project/${slug}/context`)
    .then(response => {
      if (!response.ok) throw new Error('API 调用失败');
      return response.json();
    })
    .then(data => {
      updateRunsDisplay(data.runs);
      updateMetrics(data.metrics);
    })
    .catch(err => console.error('自动刷新错误:', err));
}

function updateRunsDisplay(runs) {
  const runsList = document.getElementById('runs-list');
  if (!runsList) return;
  
  const currentRuns = runsList.querySelectorAll('.run-record-item');
  
  // 检查是否有实质性改变（运行数量不同）
  if (currentRuns.length === runs.length) {
    return;  // 没有变化，不更新
  }
  
  // 更新 runs 列表
  const newRunHtml = runs.map(run => formatRunCard(run)).join('');
  runsList.innerHTML = newRunHtml;
  
  // 保留搜索框的搜索状态（不清空）
  const searchPanel = runsList.previousElementSibling;
  const searchInput = searchPanel?.querySelector('[data-search-target]');
  if (searchInput && searchInput.value.length > 0) {
    // 如果用户之前在搜索，重新应用搜索过滤
    filterItems('.run-record-item', searchInput.value.toLowerCase(), searchPanel);
  }
}

function updateMetrics(metrics) {
  // 更新项目概况中的指标
  const metricTiles = document.querySelectorAll('.metric-tile dd');
  if (metricTiles.length >= 4) {
    metricTiles[1].textContent = metrics.outputs || 0;  // 研究产出
    metricTiles[2].textContent = metrics.open_tickets || 0;  // 待办任务
    metricTiles[3].textContent = metrics.runs || 0;  // 推进记录
  }
}

function formatRunCard(run) {
  const primaryRole = run.role_id;
  const executed = run.executed ? 'pill-ok' : 'pill-warn';
  const executedText = run.executed ? '已有产出' : '仅有本轮说明';
  
  let linksHtml = `
    <a class="button-link button-link-secondary button-link-inline" 
       href="/projects/${run.slug}/view?path=${encodeURIComponent(run.prompt_path)}">查看本轮说明</a>
  `;
  
  if (run.response_path) {
    linksHtml += `
      <a class="button-link button-link-secondary button-link-inline" 
         href="/projects/${run.slug}/view?path=${encodeURIComponent(run.response_path)}">查看结果</a>
    `;
  }
  
  return `
    <article class="run-card run-record-item">
      <div class="run-topline">
        <strong>${primaryRole}</strong>
        <span class="pill ${executed}">${executedText}</span>
      </div>
      <p>${run.task || '（无任务说明）'}</p>
      ${run.context ? `<p class="muted">参考材料：${run.context.join('、')}</p>` : ''}
      <div class="agent-links">
        ${linksHtml}
      </div>
    </article>
  `;
}

// ===== 初始化 =====
window.autoRefreshPaused = false;  // 全局标志：自动刷新是否暂停

document.addEventListener('DOMContentLoaded', () => {
  initializeCodeHighlight();
  initializeMarkdownEditor();
  initializeSearch();  // 初始化所有搜索框
  initializeAutoRefresh();
  
  // 立即加载 highlight.js（不等待交互）
  loadHighlightJs(() => {
    initializeCodeHighlight();
  });
});
