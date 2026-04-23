document.addEventListener('DOMContentLoaded', function() {
    const contentTextarea = document.getElementById('content');
    const toolbarBtns = document.querySelectorAll('.toolbar-btn');
    const categorySelect = document.getElementById('category_name');
    const categoryNew = document.getElementById('category_new');
    const tagNamesInput = document.getElementById('tag_names');
    const tagBtns = document.querySelectorAll('.tag-btn');
    const titleInput = document.getElementById('title');
    const excerptInput = document.getElementById('excerpt');
    
    toolbarBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const action = btn.dataset.action;
            insertFormat(action);
        });
    });
    
    function insertFormat(action) {
        if (!contentTextarea) return;
        
        const start = contentTextarea.selectionStart;
        const end = contentTextarea.selectionEnd;
        const value = contentTextarea.value;
        const selectedText = value.substring(start, end);
        
        let before = '';
        let after = '';
        let placeholder = '';
        
        switch (action) {
            case 'bold':
                before = '**';
                after = '**';
                placeholder = '粗体文字';
                break;
            case 'italic':
                before = '*';
                after = '*';
                placeholder = '斜体文字';
                break;
            case 'link':
                before = '[';
                after = '](https://)';
                placeholder = '链接文字';
                break;
            case 'list':
                before = '- ';
                after = '';
                placeholder = '列表项';
                break;
        }
        
        const textToInsert = selectedText || placeholder;
        const newValue = value.substring(0, start) + before + textToInsert + after + value.substring(end);
        
        contentTextarea.value = newValue;
        contentTextarea.focus();
        
        const newCursorPos = start + before.length + textToInsert.length;
        contentTextarea.setSelectionRange(newCursorPos, newCursorPos);
    }
    
    if (categoryNew && categorySelect) {
        categoryNew.addEventListener('input', function() {
            if (this.value.trim()) {
                categorySelect.value = '';
            }
        });
        
        categorySelect.addEventListener('change', function() {
            if (this.value) {
                categoryNew.value = '';
            }
        });
    }
    
    tagBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const tag = this.dataset.tag;
            addTag(tag);
        });
    });
    
    function addTag(tag) {
        if (!tagNamesInput) return;
        
        const currentValue = tagNamesInput.value.trim();
        const tags = currentValue 
            ? currentValue.split(',').map(function(t) { return t.trim(); }) 
            : [];
        
        if (!tags.includes(tag)) {
            tags.push(tag);
            tagNamesInput.value = tags.join(', ');
        }
    }
    
    if (titleInput && excerptInput) {
        titleInput.addEventListener('blur', function() {
            if (!excerptInput.value.trim() && contentTextarea.value.trim()) {
                const content = contentTextarea.value;
                const autoExcerpt = content.substring(0, 100) + (content.length > 100 ? '...' : '');
                excerptInput.placeholder = '自动生成: ' + autoExcerpt;
            }
        });
    }
    
    const postForm = document.querySelector('.post-form');
    if (postForm) {
        postForm.addEventListener('submit', function(e) {
            const title = titleInput ? titleInput.value.trim() : '';
            const content = contentTextarea ? contentTextarea.value.trim() : '';
            
            if (!title || !content) {
                e.preventDefault();
                alert('请填写文章标题和内容！');
                return;
            }
            
            if (categoryNew && categoryNew.value.trim()) {
                categorySelect.value = categoryNew.value.trim();
            }
        });
    }
});
