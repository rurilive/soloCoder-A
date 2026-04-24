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
        },
        {
            name: "球体",
            expression: "x^2 + y^2 + z^2",
            color: "#6c5ce7",
            description: "x² + y² + z² = 常数"
        }
    ];

    const DEFAULT_COLORS = [
        "#ff6b6b", "#4ecdc4", "#45b7d1", "#f9ca24", "#6c5ce7",
        "#fd79a8", "#00b894", "#e17055", "#0984e3", "#a29bfe"
    ];

    let functionCounter = 0;

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
        statusText: document.getElementById('statusText')
    };

    function init() {
        renderPresets();
        addFunction();
        bindEvents();
        
        if (window.FunctionRenderer) {
            window.FunctionRenderer.init('threeCanvas', 'canvasContainer');
        }
        
        updateStatus('就绪');
    }

    function renderPresets() {
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
        
        elements.functionsContainer.appendChild(functionItem);
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
        elements.functionsContainer.innerHTML = '';
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
            operation: elements.operationSelect.value,
            params: {
                x_min: parseFloat(elements.xMin.value) || -5,
                x_max: parseFloat(elements.xMax.value) || 5,
                y_min: parseFloat(elements.yMin.value) || -5,
                y_max: parseFloat(elements.yMax.value) || 5,
                z_min: -5,
                z_max: 5,
                resolution: parseInt(elements.resolution.value) || 50,
                isovalue: 0,
                epsilon: parseFloat(elements.epsilon.value) || 0.5
            }
        };
    }

    function updateStatus(text) {
        if (elements.statusText) {
            elements.statusText.textContent = text;
        }
    }

    function updateStats(vertices = 0, faces = 0) {
        if (elements.vertexCount) {
            elements.vertexCount.textContent = vertices.toLocaleString();
        }
        if (elements.faceCount) {
            elements.faceCount.textContent = faces.toLocaleString();
        }
    }

    async function generate() {
        const formData = collectFormData();
        
        if (formData.functions.length === 0) {
            alert('请至少输入一个函数表达式');
            return;
        }
        
        updateStatus('生成中...');
        
        try {
            const response = await fetch('/api/render', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                renderSurfaces(result.data);
                updateStatus('生成完成');
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
        elements.addFunctionBtn.addEventListener('click', function() {
            addFunction();
        });
        
        elements.resolution.addEventListener('input', function() {
            elements.resolutionValue.textContent = this.value;
        });
        
        elements.generateBtn.addEventListener('click', generate);
        elements.resetViewBtn.addEventListener('click', resetView);
        elements.clearBtn.addEventListener('click', clearAllFunctions);
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
        updateStats: updateStats
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
