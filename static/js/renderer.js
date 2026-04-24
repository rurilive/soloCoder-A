(function() {
    'use strict';

    let scene = null;
    let camera = null;
    let renderer = null;
    let controls = null;
    let canvasElement = null;
    let containerElement = null;
    let animationId = null;
    
    let surfaceMeshes = [];
    let gridHelper = null;
    let axesHelper = null;
    let isDragging = false;
    let lastMouseX = 0;
    let lastMouseY = 0;

    const DEFAULT_CAMERA_POSITION = { x: 10, y: 10, z: 10 };
    const DEFAULT_TARGET = { x: 0, y: 0, z: 0 };

    const THEMES = {
        dark: {
            background: 0x2d2d2d,
            gridPrimary: 0x444444,
            gridSecondary: 0x333333,
            axesX: 0xff4444,
            axesY: 0x44ff44,
            axesZ: 0x4444ff
        },
        light: {
            background: 0xf0f0f0,
            gridPrimary: 0xcccccc,
            gridSecondary: 0xdddddd,
            axesX: 0xcc0000,
            axesY: 0x00aa00,
            axesZ: 0x0000cc
        },
        blue: {
            background: 0x0f172a,
            gridPrimary: 0x1e3a5f,
            gridSecondary: 0x1e293b,
            axesX: 0xff6b6b,
            axesY: 0x69db7c,
            axesZ: 0x4dabf7
        },
        matrix: {
            background: 0x000000,
            gridPrimary: 0x003300,
            gridSecondary: 0x001a00,
            axesX: 0xff0000,
            axesY: 0x00ff00,
            axesZ: 0x00aa00
        },
        sunset: {
            background: 0x1a0a0a,
            gridPrimary: 0x4a2020,
            gridSecondary: 0x2d1a1a,
            axesX: 0xff6b6b,
            axesY: 0x95e1d3,
            axesZ: 0xeec0da
        }
    };

    let currentTheme = 'dark';

    let frameCount = 0;
    let lastFpsTime = performance.now();
    let currentFps = 60;
    let renderTimeMs = 0;
    let lastRenderStart = 0;

    function init(canvasId, containerId) {
        canvasElement = document.getElementById(canvasId);
        containerElement = document.getElementById(containerId);
        
        if (!canvasElement || !containerElement) {
            console.error('Canvas or container element not found');
            return false;
        }
        
        initScene();
        initCamera();
        initRenderer();
        initControls();
        initLights();
        initHelpers();
        
        window.addEventListener('resize', onWindowResize);
        
        animate();
        
        console.log('FunctionRenderer initialized');
        return true;
    }

    function initScene() {
        scene = new THREE.Scene();
        applyTheme(currentTheme);
    }

    function applyTheme(themeName) {
        if (!scene) return;
        
        currentTheme = themeName;
        const theme = THEMES[themeName] || THEMES.dark;
        
        scene.background = new THREE.Color(theme.background);
        
        if (gridHelper) {
            scene.remove(gridHelper);
            gridHelper.geometry.dispose();
            gridHelper.material.dispose();
        }
        
        gridHelper = new THREE.GridHelper(20, 20, theme.gridPrimary, theme.gridSecondary);
        gridHelper.rotation.x = Math.PI / 2;
        scene.add(gridHelper);
        
        if (axesHelper) {
            scene.remove(axesHelper);
            axesHelper.geometry.dispose();
            axesHelper.material.dispose();
        }
        
        axesHelper = new THREE.AxesHelper(5);
        scene.add(axesHelper);
    }

    function initCamera() {
        const width = containerElement.clientWidth;
        const height = containerElement.clientHeight;
        
        camera = new THREE.PerspectiveCamera(
            60,
            width / height,
            0.1,
            1000
        );
        
        camera.position.set(
            DEFAULT_CAMERA_POSITION.x,
            DEFAULT_CAMERA_POSITION.y,
            DEFAULT_CAMERA_POSITION.z
        );
    }

    function initRenderer() {
        const width = containerElement.clientWidth;
        const height = containerElement.clientHeight;
        
        renderer = new THREE.WebGLRenderer({
            canvas: canvasElement,
            antialias: true
        });
        
        renderer.setSize(width, height);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    }

    function initControls() {
        try {
            const OrbitControls = THREE.OrbitControls || window.OrbitControls;
            if (OrbitControls) {
                controls = new OrbitControls(camera, renderer.domElement);
                
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.screenSpacePanning = false;
                controls.minDistance = 1;
                controls.maxDistance = 100;
                controls.maxPolarAngle = Math.PI;
                
                controls.target.set(
                    DEFAULT_TARGET.x,
                    DEFAULT_TARGET.y,
                    DEFAULT_TARGET.z
                );
                
                controls.update();
                console.log('OrbitControls initialized successfully');
                return;
            }
        } catch (e) {
            console.warn('OrbitControls not available, using fallback controls:', e);
        }
        
        initFallbackControls();
    }

    function initFallbackControls() {
        console.log('Using fallback mouse controls');
        
        const canvas = renderer.domElement;
        let theta = Math.PI / 4;
        let phi = Math.PI / 4;
        let radius = Math.sqrt(
            DEFAULT_CAMERA_POSITION.x * DEFAULT_CAMERA_POSITION.x +
            DEFAULT_CAMERA_POSITION.y * DEFAULT_CAMERA_POSITION.y +
            DEFAULT_CAMERA_POSITION.z * DEFAULT_CAMERA_POSITION.z
        );
        
        function updateCamera() {
            camera.position.x = radius * Math.sin(phi) * Math.cos(theta);
            camera.position.y = radius * Math.cos(phi);
            camera.position.z = radius * Math.sin(phi) * Math.sin(theta);
            camera.lookAt(DEFAULT_TARGET.x, DEFAULT_TARGET.y, DEFAULT_TARGET.z);
        }
        
        canvas.addEventListener('mousedown', function(e) {
            isDragging = true;
            lastMouseX = e.clientX;
            lastMouseY = e.clientY;
            canvas.style.cursor = 'grabbing';
        });
        
        canvas.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            
            const deltaX = e.clientX - lastMouseX;
            const deltaY = e.clientY - lastMouseY;
            
            theta -= deltaX * 0.01;
            phi = Math.max(0.1, Math.min(Math.PI - 0.1, phi + deltaY * 0.01));
            
            updateCamera();
            
            lastMouseX = e.clientX;
            lastMouseY = e.clientY;
        });
        
        canvas.addEventListener('mouseup', function() {
            isDragging = false;
            canvas.style.cursor = 'grab';
        });
        
        canvas.addEventListener('mouseleave', function() {
            isDragging = false;
            canvas.style.cursor = 'grab';
        });
        
        canvas.addEventListener('wheel', function(e) {
            e.preventDefault();
            const zoomFactor = e.deltaY > 0 ? 1.1 : 0.9;
            radius = Math.max(1, Math.min(100, radius * zoomFactor));
            updateCamera();
        }, { passive: false });
        
        canvas.style.cursor = 'grab';
        
        controls = {
            update: function() {},
            target: new THREE.Vector3(DEFAULT_TARGET.x, DEFAULT_TARGET.y, DEFAULT_TARGET.z),
            dispose: function() {},
            isFallback: true
        };
        
        updateCamera();
    }

    function initLights() {
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        scene.add(ambientLight);
        
        const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight1.position.set(10, 20, 10);
        directionalLight1.castShadow = true;
        directionalLight1.shadow.mapSize.width = 2048;
        directionalLight1.shadow.mapSize.height = 2048;
        directionalLight1.shadow.camera.near = 0.5;
        directionalLight1.shadow.camera.far = 100;
        directionalLight1.shadow.camera.left = -20;
        directionalLight1.shadow.camera.right = 20;
        directionalLight1.shadow.camera.top = 20;
        directionalLight1.shadow.camera.bottom = -20;
        scene.add(directionalLight1);
        
        const directionalLight2 = new THREE.DirectionalLight(0x8888ff, 0.3);
        directionalLight2.position.set(-10, 10, -10);
        scene.add(directionalLight2);
    }

    function initHelpers() {
        const theme = THEMES[currentTheme];
        gridHelper = new THREE.GridHelper(20, 20, theme.gridPrimary, theme.gridSecondary);
        gridHelper.rotation.x = Math.PI / 2;
        scene.add(gridHelper);
        
        axesHelper = new THREE.AxesHelper(5);
        scene.add(axesHelper);
    }

    function onWindowResize() {
        if (!containerElement || !camera || !renderer) return;
        
        const width = containerElement.clientWidth;
        const height = containerElement.clientHeight;
        
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        
        renderer.setSize(width, height);
    }

    function animate() {
        animationId = requestAnimationFrame(animate);
        
        lastRenderStart = performance.now();
        
        if (controls && !controls.isFallback) {
            controls.update();
        }
        
        if (renderer && scene && camera) {
            renderer.render(scene, camera);
        }
        
        renderTimeMs = performance.now() - lastRenderStart;
        
        frameCount++;
        const now = performance.now();
        if (now - lastFpsTime >= 1000) {
            currentFps = frameCount;
            frameCount = 0;
            lastFpsTime = now;
        }
    }

    function addSurface(surfaceData, color = '#ff6b6b') {
        if (!surfaceData || !surfaceData.vertices || !surfaceData.faces) {
            console.warn('Invalid surface data');
            return null;
        }
        
        const vertices = surfaceData.vertices;
        const faces = surfaceData.faces;
        
        if (vertices.length === 0 || faces.length === 0) {
            console.warn('Empty surface data');
            return null;
        }
        
        const geometry = new THREE.BufferGeometry();
        
        const vertexPositions = [];
        const indices = [];
        
        for (let i = 0; i < vertices.length; i++) {
            const v = vertices[i];
            vertexPositions.push(v[0], v[1], v[2]);
        }
        
        for (let i = 0; i < faces.length; i++) {
            const f = faces[i];
            if (f.length === 3) {
                indices.push(f[0], f[1], f[2]);
            } else if (f.length === 4) {
                indices.push(f[0], f[1], f[2], f[0], f[2], f[3]);
            }
        }
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertexPositions, 3));
        geometry.setIndex(indices);
        geometry.computeVertexNormals();
        
        const material = new THREE.MeshPhongMaterial({
            color: new THREE.Color(color),
            side: THREE.DoubleSide,
            shininess: 30,
            specular: 0x444444,
            flatShading: false
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        
        const wireframeMaterial = new THREE.MeshBasicMaterial({
            color: 0x000000,
            wireframe: true,
            transparent: true,
            opacity: 0.1
        });
        const wireframe = new THREE.Mesh(geometry, wireframeMaterial);
        mesh.add(wireframe);
        
        scene.add(mesh);
        surfaceMeshes.push(mesh);
        
        updateStats();
        
        return mesh;
    }

    function clear() {
        for (let i = surfaceMeshes.length - 1; i >= 0; i--) {
            const mesh = surfaceMeshes[i];
            scene.remove(mesh);
            
            if (mesh.geometry) {
                mesh.geometry.dispose();
            }
            
            if (mesh.material) {
                if (Array.isArray(mesh.material)) {
                    mesh.material.forEach(m => m.dispose());
                } else {
                    mesh.material.dispose();
                }
            }
        }
        
        surfaceMeshes = [];
        updateStats();
    }

    function resetCamera() {
        if (camera) {
            camera.position.set(
                DEFAULT_CAMERA_POSITION.x,
                DEFAULT_CAMERA_POSITION.y,
                DEFAULT_CAMERA_POSITION.z
            );
            
            if (controls && !controls.isFallback) {
                controls.target.set(
                    DEFAULT_TARGET.x,
                    DEFAULT_TARGET.y,
                    DEFAULT_TARGET.z
                );
                controls.update();
            } else {
                camera.lookAt(DEFAULT_TARGET.x, DEFAULT_TARGET.y, DEFAULT_TARGET.z);
            }
        }
    }

    function updateStats() {
        let totalVertices = 0;
        let totalFaces = 0;
        
        surfaceMeshes.forEach(mesh => {
            if (mesh.geometry) {
                const posAttr = mesh.geometry.getAttribute('position');
                if (posAttr) {
                    totalVertices += posAttr.count;
                }
                
                const indexAttr = mesh.geometry.getIndex();
                if (indexAttr) {
                    totalFaces += indexAttr.count / 3;
                }
            }
        });
        
        if (window.App && window.App.updateStats) {
            window.App.updateStats(totalVertices, Math.floor(totalFaces));
        }
    }

    function getPerformanceData() {
        return {
            fps: currentFps,
            renderTimeMs: renderTimeMs
        };
    }

    function dispose() {
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
        
        clear();
        
        if (gridHelper) {
            scene.remove(gridHelper);
            gridHelper.geometry.dispose();
            gridHelper.material.dispose();
            gridHelper = null;
        }
        
        if (axesHelper) {
            scene.remove(axesHelper);
            axesHelper.geometry.dispose();
            axesHelper.material.dispose();
            axesHelper = null;
        }
        
        if (renderer) {
            renderer.dispose();
            renderer = null;
        }
        
        if (controls && controls.dispose) {
            controls.dispose();
            controls = null;
        }
        
        scene = null;
        camera = null;
        canvasElement = null;
        containerElement = null;
        
        window.removeEventListener('resize', onWindowResize);
    }

    window.FunctionRenderer = {
        init: init,
        addSurface: addSurface,
        clear: clear,
        resetCamera: resetCamera,
        dispose: dispose,
        getScene: function() { return scene; },
        getCamera: function() { return camera; },
        getRenderer: function() { return renderer; },
        getControls: function() { return controls; },
        applyTheme: applyTheme,
        getPerformanceData: getPerformanceData
    };

})();
