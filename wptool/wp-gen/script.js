document.addEventListener("DOMContentLoaded", function() {
    // Chức năng chuyển đổi tab
    const tabItems = document.querySelectorAll('.tab-item');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabItems.forEach(item => {
      item.addEventListener('click', function() {
        const target = this.getAttribute('data-target');
        // Xóa active ở tất cả tab
        tabItems.forEach(i => i.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        // Thêm active cho tab được chọn và nội dung tương ứng
        this.classList.add('active');
        document.getElementById(target).classList.add('active');
      });
    });
    
    // Repeater cho Tax Query
    const addTaxQueryBtn = document.getElementById('addTaxQuery');
    if(addTaxQueryBtn){
      addTaxQueryBtn.addEventListener('click', function(){
        const container = document.createElement('div');
        container.className = 'tax-query-item repeater-item';
        container.innerHTML = `
          <div class="form-group">
            <label>Taxonomy</label>
            <input type="text" class="tax-taxonomy" placeholder="Taxonomy slug">
          </div>
          <div class="form-group">
            <label>Field</label>
            <select class="tax-field">
              <option value="">Select...</option>
              <option value="term_id">Term ID</option>
              <option value="name">Name</option>
              <option value="slug">Slug</option>
              <option value="term_taxonomy_id">Term taxonomy ID</option>
            </select>
          </div>
          <div class="form-group">
            <label>Taxonomy term(s)</label>
            <input type="text" class="tax-terms" placeholder="Comma-separated terms">
          </div>
          <div class="form-group">
            <label>Operator</label>
            <select class="tax-operator">
              <option value="">Select...</option>
              <option value="IN">IN</option>
              <option value="NOT IN">NOT IN</option>
              <option value="AND">AND</option>
              <option value="EXISTS">EXISTS</option>
              <option value="NOT EXISTS">NOT EXISTS</option>
            </select>
          </div>
          <button class="remove-item">Remove</button>
        `;
        document.getElementById('taxQueryList').appendChild(container);
        
        container.querySelector('.remove-item').addEventListener('click', function(){
          container.remove();
        });
      });
    }
    
    // Repeater cho Meta Query
    const addMetaQueryBtn = document.getElementById('addMetaQuery');
    if(addMetaQueryBtn){
      addMetaQueryBtn.addEventListener('click', function(){
        const container = document.createElement('div');
        container.className = 'meta-query-item repeater-item';
        container.innerHTML = `
          <div class="form-group">
            <label>Meta Key</label>
            <input type="text" class="meta-key" placeholder="Meta key">
          </div>
          <div class="form-group">
            <label>Meta Value</label>
            <input type="text" class="meta-value" placeholder="Meta value">
          </div>
          <div class="form-group">
            <label>Compare</label>
            <select class="meta-compare">
              <option value="">Select...</option>
              <option value="=">=</option>
              <option value="!=">!=</option>
              <option value=">">></option>
              <option value=">=">>=</option>
              <option value="<"><</option>
              <option value="<="><=</option>
            </select>
          </div>
          <button class="remove-item">Remove</button>
        `;
        document.getElementById('metaQueryList').appendChild(container);
        
        container.querySelector('.remove-item').addEventListener('click', function(){
          container.remove();
        });
      });
    }
    
    // Repeater cho Date Query
    const addDateQueryBtn = document.getElementById('addDateQuery');
    if(addDateQueryBtn){
      addDateQueryBtn.addEventListener('click', function(){
        const container = document.createElement('div');
        container.className = 'date-query-item repeater-item';
        container.innerHTML = `
          <div class="form-group">
            <label>Column</label>
            <input type="text" class="date-column" placeholder="e.g. post_date">
          </div>
          <div class="form-group">
            <label>After</label>
            <input type="text" class="date-after" placeholder="YYYY-MM-DD">
          </div>
          <div class="form-group">
            <label>Before</label>
            <input type="text" class="date-before" placeholder="YYYY-MM-DD">
          </div>
          <div class="form-group checkbox-group">
            <input type="checkbox" class="date-inclusive" id="inclusive-${Date.now()}">
            <label for="inclusive-${Date.now()}">Inclusive</label>
          </div>
          <button class="remove-item">Remove</button>
        `;
        document.getElementById('dateQueryList').appendChild(container);
        
        container.querySelector('.remove-item').addEventListener('click', function(){
          container.remove();
        });
      });
    }
  });
  document.addEventListener("DOMContentLoaded", function() {
    const switcherItems = document.querySelectorAll('.wp-query-switcher__item');
    const contents = document.querySelectorAll('.wp-query-result__content');
    const copyBtnJson = document.getElementById('copyBtn-json');
    const copyBtnPhp = document.getElementById('copyBtn-php');
    const resetBtnJson = document.getElementById('resetBtn-json');
    const resetBtnPhp = document.getElementById('resetBtn-php');
  
    // Chuyển đổi giữa tab JSON và PHP
    switcherItems.forEach(item => {
      item.addEventListener('click', function() {
        // Loại bỏ active và ẩn toàn bộ nội dung, nút hành động
        switcherItems.forEach(s => s.classList.remove('active'));
        contents.forEach(c => c.classList.add('hide'));
        copyBtnJson.classList.add('hide');
        resetBtnJson.classList.add('hide');
        copyBtnPhp.classList.add('hide');
        resetBtnPhp.classList.add('hide');
  
        // Hiển thị tab được chọn
        this.classList.add('active');
        const target = this.getAttribute('data-target');
        document.getElementById(target).classList.remove('hide');
  
        // Hiển thị các nút tương ứng với tab
        if (target === 'result-json') {
          copyBtnJson.classList.remove('hide');
          resetBtnJson.classList.remove('hide');
        } else if (target === 'result-php') {
          copyBtnPhp.classList.remove('hide');
          resetBtnPhp.classList.remove('hide');
        }
      });
    });
  
    // Copy nội dung vào Clipboard
    copyBtnJson.addEventListener('click', function() {
      const text = document.getElementById('result-json').textContent;
      navigator.clipboard.writeText(text).then(() => {
        alert('Copied JSON to clipboard!');
      });
    });
  
    copyBtnPhp.addEventListener('click', function() {
      const text = document.getElementById('result-php').textContent;
      navigator.clipboard.writeText(text).then(() => {
        alert('Copied PHP to clipboard!');
      });
    });
  
    // Reset nội dung Generated Query (ví dụ: xóa nội dung hiện tại)
    function resetContent(contentId) {
      document.getElementById(contentId).textContent = "";
    }
  
    resetBtnJson.addEventListener('click', function() {
      resetContent('result-json');
    });
  
    resetBtnPhp.addEventListener('click', function() {
      resetContent('result-php');
    });
  });
  