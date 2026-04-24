(function() {
    'use strict';

    const PRESETS = [
        {
            name: "抛物面",
            expression: "x^2 + y^2",
            color: "#ff6b6b",
            description: "z = x² + y²"
        },
        {
            name: "正弦波",
            expression: "sin(x) * cos(y)",
            color: "#4ecdc4",
            description: "z = sin(x)·cos(y)"
        },
        {
            name: "高斯函数",
            expression: "exp(-x^2 - y^2)",
            color: "#45b7d1",
            description: "z = e^(-x²-y²)"
        },
        {
            name: "马鞍面",
            expression: "x^2 - y^2",
            color: "#f9ca24",
            description: "z = x² - y²"
        }
    ];

    const DEFAULT_COLORS = [
        "#ff6b6b", "#4ecdc4", "#45b7d1", "#f9ca24", "#6c5ce7",
        "#fd79a8", "#00b894", "#e17055", "#0984e3", "#a29bfe"
    ];

    const STORAGE_KEYS = {
        THEME: 'functionVisualizer_theme'
    };

    let functionCounter = 0;
    let lastApiTimeMs = null;
    let totalVertices = 0;
    let totalFaces = 0;
    let perfPanelVisible = false;
    let perfUpdateInterval = null;

    const elements = {
        presetsContainer: document.getElementById('presetsContainer'),
        functionsContainer: document.getElementById('functionsContainer'),
        addFunctionBtn: document.getElementById('addFunctionBtn'),
        operationSelect: document.getElementById('operationSelect'),
        xMin: document.getElementById('xMin'),
        xMax: document.getElementById('xMax'),
        yMin: document.getElementById('yMin'),
        yMax: document.getElementById('yMax'),
        resolution: document.getElementById('resolution'),
        resolutionValue: document.getElementById('resolutionValue'),
        epsilon: document.getElementById('epsilon'),
        generateBtn: document.getElementById('generateBtn'),
        resetViewBtn: document.getElementById('resetViewBtn'),
        clearBtn: document.getElementById('clearBtn'),
        vertexCount: document.getElementById('vertexCount'),
        faceCount: document.getElementById('faceCount'),
        statusText: document.getElementById('statusText'),
        themeSelect: document.getElementById('themeSelect'),
        performancePanel: document.getElementById('performancePanel'),
        perfToggleBtn: document.getElementById('perfToggleBtn'),
        perfFps: document.getElementById('perfFps'),
        perfRender: document.getElementById('perfRender'),
        perfApi: document.getElementById('perfApi'),
        perfVertices: document.getElementById('perfVertices'),
        perfFaces: document.getElementById('perfFaces'),
        perfBottleneck: document.getElementById('perfBottleneck')
    };

    function init() {
        loadTheme();
        renderPresets();
        addFunction();
        bindEvents();
        
        if (window.FunctionRenderer) {
            window.FunctionRenderer.init('threeCanvas', 'canvasContainer');
        }
        
        updateStatus('就绪');
        
        perfUpdateInterval = setInterval(updatePerformancePanel, 100);
    }

    function loadTheme() {
        const savedTheme = localStorage.getItem(STORAGE_KEYS.THEME) || 'dark';
        
        if (elements.themeSelect) {
            elements.themeSelect.value = savedTheme;
        }
        
        applyTheme(savedTheme);
    }

    function saveTheme(theme) {
        localStorage.setItem(STORAGE_KEYS.THEME, theme);
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        if (window.FunctionRenderer && window.FunctionRenderer.applyTheme) {
            window.FunctionRenderer.applyTheme(theme);
        }
        
        saveTheme(theme);
    }

    function renderPresets() {
        if (!elements.presetsContainer) return;
        
        elements.presetsContainer.innerHTML = '';
        
        PRESETS.forEach(preset => {
            const btn = document.createElement('button');
            btn.className = 'preset-btn';
            btn.style.setProperty('--preset-color', preset.color);
            btn.innerHTML = preset.name;
            btn.setAttribute('data-expression', preset.expression);
            btn.setAttribute('data-color', preset.color);
            btn.setAttribute('data-name', preset.name);
            btn.style.setProperty('--preset-color', preset.color);
            
            btn.addEventListener('click', function() {
                const expression = this.getAttribute('data-expression');
                const color = this.getAttribute('data-color');
                const name = this.getAttribute('data-name');
                applyPreset(expression, color, name);
            });
            
            elements.presetsContainer.appendChild(btn);
        });

        const style = document.createElement('style');
        style.textContent = `
            .preset-btn::before {
                background-color: var(--preset-color);
            }
        `;
        document.head.appendChild(style);
    }

    function applyPreset(expression, color, name) {
        const functionItems = document.querySelectorAll('.function-item');
        
        if (functionItems.length === 0) {
            addFunction(expression, color, name);
        } else {
            const lastItem = functionItems[functionItems.length - 1];
            const exprInput = lastItem.querySelector('.function-expression');
            const colorInput = lastItem.querySelector('.function-color');
            const nameInput = lastItem.querySelector('.function-name');
            
            if (exprInput) exprInput.value = expression;
            if (colorInput) colorInput.value = color;
            if (nameInput && name) nameInput.value = name;
        }
    }

    function addFunction(expression = '', color = '', name = '') {
        functionCounter++;
        const index = functionCounter;
        
        if (!color) {
            color = DEFAULT_COLORS[(index - 1) % DEFAULT_COLORS.length];
        }
        
        const functionItem = document.createElement('div');
        functionItem.className = 'function-item';
        functionItem.setAttribute('data-index', index);
        
        functionItem.innerHTML = `
            <div class="function-row">
                <input type="text" class="function-name" placeholder="函数名" value="${name || ''}">
                <input type="color" class="function-color" value="${color}">
            </div>
            <div class="function-row">
                <input type="text" class="function-expression" placeholder="如: x^2 + y^2" value="${expression}">
                <button type="button" class="delete-btn" data-index="${index}">删除</button>
            </div>
        `;
        
        const deleteBtn = functionItem.querySelector('.delete-btn');
        deleteBtn.addEventListener('click', function() {
            const idx = this.getAttribute('data-index');
            removeFunction(idx);
        });
        
        if (elements.functionsContainer) {
            elements.functionsContainer.appendChild(functionItem);
        }
    }

    function removeFunction(index) {
        const functionItem = document.querySelector(`.function-item[data-index="${index}"]`);
        if (functionItem) {
            functionItem.remove();
        }
        
        const remainingItems = document.querySelectorAll('.function-item');
        if (remainingItems.length === 0) {
            functionCounter = 0;
        }
    }

    function clearAllFunctions() {
        if (elements.functionsContainer) {
            elements.functionsContainer.innerHTML = '';
        }
        functionCounter = 0;
        addFunction();
    }

    function collectFormData() {
        const functionItems = document.querySelectorAll('.function-item');
        const functions = [];
        
        functionItems.forEach(item => {
            const nameInput = item.querySelector('.function-name');
            const exprInput = item.querySelector('.function-expression');
            const colorInput = item.querySelector('.function-color');
            
            const expression = exprInput ? exprInput.value.trim() : '';
            
            if (expression) {
                functions.push({
                    name: nameInput ? nameInput.value.trim() : '',
                    expression: expression,
                    color: colorInput ? colorInput.value : '#ff6b6b'
                });
            }
        });
        
        return {
            functions: functions,
            operation: elements.operationSelect ? elements.operationSelect.value : 'none',
            params: {
                x_min: parseFloat(elements.xMin ? elements.xMin.value : -5) || -5,
                x_max: parseFloat(elements.xMax ? elements.xMax.value : 5) || 5,
                y_min: parseFloat(elements.yMin ? elements.yMin.value : -5) || -5,
                y_max: parseFloat(elements.yMax ? elements.yMax.value : 5) || 5,
                z_min: -5,
                z_max: 5,
                resolution: parseInt(elements.resolution ? elements.resolution.value : 50) || 50,
                isovalue: 0,
                epsilon: parseFloat(elements.epsilon ? elements.epsilon.value : 0.5) || 0.5
            }
        };
    }

    function updateStatus(text) {
        if (elements.statusText) {
            elements.statusText.textContent = text;
        }
    }

    function updateStats(vertices = 0, faces = 0) {
        totalVertices = vertices;
        totalFaces = faces;
        
        if (elements.vertexCount) {
            elements.vertexCount.textContent = vertices.toLocaleString();
        }
        if (elements.faceCount) {
            elements.faceCount.textContent = faces.toLocaleString();
        }
    }

    function updatePerformancePanel() {
        if (!perfPanelVisible) return;
        
        let perfData = { fps: 60, renderTimeMs: 0.5 };
        if (window.FunctionRenderer && window.FunctionRenderer.getPerformanceData) {
            perfData = window.FunctionRenderer.getPerformanceData();
        }
        
        const fps = perfData.fps || 60;
        const renderMs = perfData.renderTimeMs || 0;
        
        if (elements.perfFps) {
            elements.perfFps.textContent = fps;
            elements.perfFps.className = 'performance-value ' + getFpsClass(fps);
        }
        
        if (elements.perfRender) {
            elements.perfRender.textContent = renderMs.toFixed(2) + 'ms';
            elements.perfRender.className = 'performance-value ' + getRenderTimeClass(renderMs);
        }
        
        if (elements.perfApi) {
            elements.perfApi.textContent = lastApiTimeMs ? lastApiTimeMs.toFixed(1) + 'ms' : '-';
            elements.perfApi.className = 'performance-value ' + getApiTimeClass(lastApiTimeMs);
        }
        
        if (elements.perfVertices) {
            elements.perfVertices.textContent = totalVertices.toLocaleString();
        }
        
        if (elements.perfFaces) {
            elements.perfFaces.textContent = totalFaces.toLocaleString();
        }
        
        if (elements.perfBottleneck) {
            elements.perfBottleneck.textContent = analyzeBottleneck(fps, renderMs, lastApiTimeMs, totalVertices);
        }
    }

    function getFpsClass(fps) {
        if (fps >= 50) return 'good';
        if (fps >= 30) return 'warning';
        return 'bad';
    }

    function getRenderTimeClass(ms) {
        if (ms <= 5) return 'good';
        if (ms <= 16) return 'warning';
        return 'bad';
    }

    function getApiTimeClass(ms) {
        if (ms === null || ms === undefined) return '';
        if (ms <= 50) return 'good';
        if (ms <= 200) return 'warning';
        return 'bad';
    }

    function analyzeBottleneck(fps, renderMs, apiMs, vertices) {
        const bottlenecks = [];
        
        if (vertices > 50000) {
            bottlenecks.push('顶点数量过高 (' + vertices.toLocaleString() + ')');
        } else if (vertices > 20000) {
            bottlenecks.push('中等顶点数 (' + vertices.toLocaleString() + ')');
        }
        
        if (renderMs > 16) {
            bottlenecks.push('GPU渲染慢 (' + renderMs.toFixed(1) + 'ms)');
        } else if (renderMs > 5) {
            bottlenecks.push('GPU渲染正常');
        }
        
        if (apiMs > 200) {
            bottlenecks.push('后端计算慢 (' + apiMs.toFixed(0) + 'ms)');
        } else if (apiMs > 50) {
            bottlenecks.push('后端正常');
        }
        
        if (fps < 30) {
            bottlenecks.push('帧率过低 (' + fps + ' FPS)');
        } else if (fps < 50) {
            bottlenecks.push('帧率中等 (' + fps + ' FPS)');
        }
        
        if (bottlenecks.length === 0) {
            if (vertices === 0) {
                return '无模型加载';
            }
            return '性能良好';
        }
        
        return bottlenecks[0];
    }

    function togglePerformancePanel() {
        perfPanelVisible = !perfPanelVisible;
        
        if (elements.performancePanel) {
            if (perfPanelVisible) {
                elements.performancePanel.classList.remove('hidden');
                if (elements.perfToggleBtn) {
                    elements.perfToggleBtn.textContent = '✕ 关闭';
                }
            } else {
                elements.performancePanel.classList.add('hidden');
                if (elements.perfToggleBtn) {
                    elements.perfToggleBtn.textContent = '📊 性能';
                }
            }
        }
    }

    async function generate() {
        const formData = collectFormData();
        
        if (formData.functions.length === 0) {
            alert('请至少输入一个函数表达式');
            return;
        }
        
        updateStatus('生成中...');
        
        const apiStartTime = performance.now();
        
        try {
            const response = await fetch('/api/render', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            lastApiTimeMs = performance.now() - apiStartTime;
            
            const result = await response.json();
            
            if (result.success) {
                renderSurfaces(result.data);
                updateStatus('生成完成 (' + lastApiTimeMs.toFixed(0) + 'ms)');
            } else {
                const errorMsg = result.error || '生成失败';
                updateStatus('错误: ' + errorMsg);
                alert(errorMsg);
            }
        } catch (error) {
            console.error('请求错误:', error);
            updateStatus('网络错误');
            alert('网络请求失败，请检查服务器是否运行');
        }
    }

    function renderSurfaces(data) {
        if (window.FunctionRenderer && window.FunctionRenderer.clear) {
            window.FunctionRenderer.clear();
        }
        
        if (window.FunctionRenderer && window.FunctionRenderer.addSurface) {
            if (data.type === 'multiple' && data.surfaces) {
                data.surfaces.forEach((surface, index) => {
                    window.FunctionRenderer.addSurface(surface, surface.color);
                });
            } else if (data.type === 'single' && data.surface) {
                window.FunctionRenderer.addSurface(data.surface, '#ff6b6b');
            } else if (data.vertices && data.faces) {
                window.FunctionRenderer.addSurface(data, '#ff6b6b');
            }
        }
    }

    function resetView() {
        if (window.FunctionRenderer && window.FunctionRenderer.resetCamera) {
            window.FunctionRenderer.resetCamera();
        }
        updateStatus('视图已重置');
    }

    function bindEvents() {
        if (elements.addFunctionBtn) {
            elements.addFunctionBtn.addEventListener('click', function() {
                addFunction();
            });
        }
        
        if (elements.resolution) {
            elements.resolution.addEventListener('input', function() {
                if (elements.resolutionValue) {
                    elements.resolutionValue.textContent = this.value;
                }
            });
        }
        
        if (elements.generateBtn) {
            elements.generateBtn.addEventListener('click', generate);
        }
        if (elements.resetViewBtn) {
            elements.resetViewBtn.addEventListener('click', resetView);
        }
        if (elements.clearBtn) {
            elements.clearBtn.addEventListener('click', clearAllFunctions);
        }
        
        if (elements.themeSelect) {
            elements.themeSelect.addEventListener('change', function() {
                applyTheme(this.value);
            });
        }
        
        if (elements.perfToggleBtn) {
            elements.perfToggleBtn.addEventListener('click', togglePerformancePanel);
        }
    }

    window.App = {
        init: init,
        collectFormData: collectFormData,
        addFunction: addFunction,
        removeFunction: removeFunction,
        clearAllFunctions: clearAllFunctions,
        generate: generate,
        resetView: resetView,
        updateStatus: updateStatus,
        updateStats: updateStats,
        applyTheme: applyTheme,
        togglePerformancePanel: togglePerformancePanel,
        getLastApiTime: function() { return lastApiTimeMs; }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
