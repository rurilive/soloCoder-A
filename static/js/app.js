class DiaryApp {
    constructor() {
        this.currentDiaryId = null;
        this.selectedFiles = [];
        this.existingImages = [];
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // 新建日记按钮
        const newDiaryBtn = document.getElementById('newDiaryBtn');
        if (newDiaryBtn) {
            newDiaryBtn.addEventListener('click', () => this.openModal());
        }

        // 关闭模态框
        const closeModal = document.getElementById('closeModal');
        if (closeModal) {
            closeModal.addEventListener('click', () => this.closeModal());
        }

        const cancelBtn = document.getElementById('cancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeModal());
        }

        // 点击模态框外部关闭
        const diaryModal = document.getElementById('diaryModal');
        if (diaryModal) {
            diaryModal.addEventListener('click', (e) => {
                if (e.target === diaryModal) {
                    this.closeModal();
                }
            });
        }

        // 图片上传预览
        const diaryImages = document.getElementById('diaryImages');
        if (diaryImages) {
            diaryImages.addEventListener('change', (e) => this.handleImageSelect(e));
        }

        // 图片拖拽上传
        const imageUploadArea = document.querySelector('.image-upload-area');
        if (imageUploadArea) {
            imageUploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                imageUploadArea.style.borderColor = '#667eea';
                imageUploadArea.style.background = '#f8f9ff';
            });

            imageUploadArea.addEventListener('dragleave', () => {
                imageUploadArea.style.borderColor = '#ddd';
                imageUploadArea.style.background = '#fafafa';
            });

            imageUploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                imageUploadArea.style.borderColor = '#ddd';
                imageUploadArea.style.background = '#fafafa';
                
                const files = Array.from(e.dataTransfer.files).filter(file => 
                    file.type.startsWith('image/')
                );
                this.handleDroppedImages(files);
            });
        }

        // 表单提交
        const diaryForm = document.getElementById('diaryForm');
        if (diaryForm) {
            diaryForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // 日记列表操作（编辑/删除）
        const diaryItems = document.getElementById('diaryItems');
        if (diaryItems) {
            diaryItems.addEventListener('click', (e) => {
                const target = e.target.closest('button[data-action]');
                if (!target) return;

                const diaryCard = target.closest('.diary-card');
                if (!diaryCard) return;

                const diaryId = diaryCard.dataset.id;
                const action = target.dataset.action;

                if (action === 'edit') {
                    this.editDiary(diaryId, diaryCard);
                } else if (action === 'delete') {
                    this.confirmDelete(diaryId);
                }
            });
        }

        // 删除确认模态框
        const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
        if (cancelDeleteBtn) {
            cancelDeleteBtn.addEventListener('click', () => this.closeDeleteModal());
        }

        const deleteModal = document.getElementById('deleteModal');
        if (deleteModal) {
            deleteModal.addEventListener('click', (e) => {
                if (e.target === deleteModal) {
                    this.closeDeleteModal();
                }
            });
        }

        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => this.deleteDiary());
        }
    }

    openModal(diaryData = null) {
        const modal = document.getElementById('diaryModal');
        const modalTitle = document.getElementById('modalTitle');
        const form = document.getElementById('diaryForm');
        const imagePreviewContainer = document.getElementById('imagePreviewContainer');

        if (diaryData) {
            this.currentDiaryId = diaryData.id;
            if (modalTitle) modalTitle.textContent = '编辑日记';
            
            // 填充表单数据
            const titleInput = document.getElementById('diaryTitle');
            const contentInput = document.getElementById('diaryContent');
            if (titleInput) titleInput.value = diaryData.title || '';
            if (contentInput) contentInput.value = diaryData.content || '';
            
            // 保存现有图片
            this.existingImages = diaryData.images || [];
            
            // 显示现有图片预览
            if (imagePreviewContainer) {
                imagePreviewContainer.innerHTML = '';
                this.existingImages.forEach((img, index) => {
                    this.addExistingImagePreview(img, index);
                });
            }
        } else {
            this.currentDiaryId = null;
            if (modalTitle) modalTitle.textContent = '写新日记';
            if (form) form.reset();
            this.existingImages = [];
            if (imagePreviewContainer) imagePreviewContainer.innerHTML = '';
        }

        this.selectedFiles = [];

        if (modal) {
            modal.classList.add('active');
        }
    }

    closeModal() {
        const modal = document.getElementById('diaryModal');
        const form = document.getElementById('diaryForm');
        const imagePreviewContainer = document.getElementById('imagePreviewContainer');

        if (modal) {
            modal.classList.remove('active');
        }
        if (form) form.reset();
        if (imagePreviewContainer) imagePreviewContainer.innerHTML = '';
        
        this.currentDiaryId = null;
        this.selectedFiles = [];
        this.existingImages = [];
    }

    handleImageSelect(e) {
        const files = Array.from(e.target.files);
        this.handleDroppedImages(files);
    }

    handleDroppedImages(files) {
        const imagePreviewContainer = document.getElementById('imagePreviewContainer');
        if (!imagePreviewContainer) return;

        files.forEach(file => {
            if (!file.type.startsWith('image/')) return;

            const reader = new FileReader();
            reader.onload = (e) => {
                this.selectedFiles.push(file);
                this.addImagePreview(e.target.result, this.selectedFiles.length - 1, false);
            };
            reader.readAsDataURL(file);
        });
    }

    addImagePreview(src, index, isExisting) {
        const imagePreviewContainer = document.getElementById('imagePreviewContainer');
        if (!imagePreviewContainer) return;

        const previewDiv = document.createElement('div');
        previewDiv.className = 'image-preview';
        previewDiv.dataset.index = index;
        previewDiv.dataset.existing = isExisting ? 'true' : 'false';

        const img = document.createElement('img');
        img.src = src;
        img.alt = '预览图片';

        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.innerHTML = '&times;';
        removeBtn.addEventListener('click', () => {
            this.removeImage(index, isExisting);
            previewDiv.remove();
        });

        previewDiv.appendChild(img);
        previewDiv.appendChild(removeBtn);
        imagePreviewContainer.appendChild(previewDiv);
    }

    addExistingImagePreview(src, index) {
        this.addImagePreview(src, index, true);
    }

    removeImage(index, isExisting) {
        if (isExisting) {
            this.existingImages.splice(index, 1);
        } else {
            this.selectedFiles.splice(index, 1);
        }
    }

    editDiary(diaryId, diaryCard) {
        // 从 DOM 中提取日记数据
        const title = diaryCard.querySelector('h3')?.textContent || '';
        const content = diaryCard.querySelector('.diary-content-preview p')?.textContent || '';
        
        // 提取图片
        const images = [];
        const imgElements = diaryCard.querySelectorAll('.diary-image');
        imgElements.forEach(img => {
            images.push(img.src);
        });

        this.openModal({
            id: diaryId,
            title: title,
            content: content,
            images: images
        });
    }

    confirmDelete(diaryId) {
        this.currentDiaryId = diaryId;
        const deleteModal = document.getElementById('deleteModal');
        if (deleteModal) {
            deleteModal.classList.add('active');
        }
    }

    closeDeleteModal() {
        this.currentDiaryId = null;
        const deleteModal = document.getElementById('deleteModal');
        if (deleteModal) {
            deleteModal.classList.remove('active');
        }
    }

    async deleteDiary() {
        if (!this.currentDiaryId) return;

        try {
            const response = await fetch(`/api/diaries/${this.currentDiaryId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                // 从 DOM 中移除
                const diaryCard = document.querySelector(`.diary-card[data-id="${this.currentDiaryId}"]`);
                if (diaryCard) {
                    diaryCard.style.animation = 'slideUp 0.3s ease reverse';
                    setTimeout(() => {
                        diaryCard.remove();
                        this.checkEmptyState();
                    }, 300);
                }

                this.showToast('日记删除成功', 'success');
            } else {
                const data = await response.json();
                this.showToast(data.message || '删除失败', 'error');
            }
        } catch (error) {
            console.error('删除失败:', error);
            this.showToast('删除失败，请稍后重试', 'error');
        }

        this.closeDeleteModal();
    }

    async handleSubmit(e) {
        e.preventDefault();

        const titleInput = document.getElementById('diaryTitle');
        const contentInput = document.getElementById('diaryContent');

        const title = titleInput?.value.trim();
        const content = contentInput?.value.trim();

        if (!title) {
            this.showToast('请输入标题', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('title', title);
        formData.append('content', content);

        // 添加选中的文件
        this.selectedFiles.forEach(file => {
            formData.append('images', file);
        });

        try {
            let response;
            
            if (this.currentDiaryId) {
                // 更新日记
                response = await fetch(`/api/diaries/${this.currentDiaryId}`, {
                    method: 'PUT',
                    body: formData
                });
            } else {
                // 创建新日记
                response = await fetch('/api/diaries', {
                    method: 'POST',
                    body: formData
                });
            }

            if (response.ok) {
                const data = await response.json();
                this.closeModal();
                
                if (this.currentDiaryId) {
                    // 更新现有条目
                    this.updateDiaryInDOM(data.diary);
                    this.showToast('日记更新成功', 'success');
                } else {
                    // 添加新条目
                    this.addDiaryToDOM(data.diary);
                    this.showToast('日记创建成功', 'success');
                }
            } else {
                const errorData = await response.json();
                this.showToast(errorData.message || '保存失败', 'error');
            }
        } catch (error) {
            console.error('提交失败:', error);
            this.showToast('保存失败，请稍后重试', 'error');
        }
    }

    addDiaryToDOM(diary) {
        const diaryItems = document.getElementById('diaryItems');
        if (!diaryItems) return;

        // 检查是否为空状态
        const emptyState = diaryItems.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }

        const diaryCard = this.createDiaryCard(diary);
        diaryItems.insertBefore(diaryCard, diaryItems.firstChild);

        // 添加入场动画
        diaryCard.style.opacity = '0';
        diaryCard.style.transform = 'translateY(20px)';
        setTimeout(() => {
            diaryCard.style.transition = 'all 0.3s ease';
            diaryCard.style.opacity = '1';
            diaryCard.style.transform = 'translateY(0)';
        }, 10);
    }

    updateDiaryInDOM(diary) {
        const diaryCard = document.querySelector(`.diary-card[data-id="${diary.id}"]`);
        if (!diaryCard) return;

        // 更新标题
        const titleEl = diaryCard.querySelector('h3');
        if (titleEl) titleEl.textContent = diary.title;

        // 更新内容
        const contentEl = diaryCard.querySelector('.diary-content-preview p');
        if (contentEl) {
            const preview = diary.content.length > 200 
                ? diary.content.substring(0, 200) + '...' 
                : diary.content;
            contentEl.textContent = preview;
        }

        // 更新图片
        const imagesContainer = diaryCard.querySelector('.diary-images');
        if (imagesContainer) {
            imagesContainer.innerHTML = '';
            diary.images.forEach(img => {
                const imgEl = document.createElement('img');
                imgEl.src = img;
                imgEl.alt = '日记图片';
                imgEl.className = 'diary-image';
                imagesContainer.appendChild(imgEl);
            });
        }

        // 更新时间
        const dateEl = diaryCard.querySelector('.diary-date');
        if (dateEl) dateEl.textContent = diary.updated_at;

        // 添加更新动画
        diaryCard.style.boxShadow = '0 0 0 2px #667eea';
        setTimeout(() => {
            diaryCard.style.boxShadow = '';
        }, 2000);
    }

    createDiaryCard(diary) {
        const card = document.createElement('div');
        card.className = 'diary-card';
        card.dataset.id = diary.id;

        const preview = diary.content.length > 200 
            ? diary.content.substring(0, 200) + '...' 
            : diary.content;

        let imagesHtml = '';
        if (diary.images && diary.images.length > 0) {
            imagesHtml = '<div class="diary-images">';
            diary.images.forEach(img => {
                imagesHtml += `<img src="${img}" alt="日记图片" class="diary-image">`;
            });
            imagesHtml += '</div>';
        }

        card.innerHTML = `
            <div class="diary-header">
                <h3>${diary.title}</h3>
                <div class="diary-actions">
                    <button class="btn btn-edit" data-action="edit">✏️</button>
                    <button class="btn btn-delete" data-action="delete">🗑️</button>
                </div>
            </div>
            <div class="diary-meta">
                <span class="diary-date">${diary.created_at}</span>
            </div>
            <div class="diary-content-preview">
                <p>${preview}</p>
            </div>
            ${imagesHtml}
        `;

        return card;
    }

    checkEmptyState() {
        const diaryItems = document.getElementById('diaryItems');
        if (!diaryItems) return;

        const diaryCards = diaryItems.querySelectorAll('.diary-card');
        if (diaryCards.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = '<p>还没有日记，点击上方按钮开始写第一篇日记吧！</p>';
            diaryItems.appendChild(emptyState);
        }
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        if (!toast) return;

        toast.textContent = message;
        toast.className = `toast ${type} show`;

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new DiaryApp();
});
