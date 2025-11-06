// =========================
// ZAKIA ADMIN PANEL SCRIPT
// =========================

(function () {
  document.addEventListener('DOMContentLoaded', () => {

    const CONFIG = {
      API_BASE: 'http://127.0.0.1:5000/admin/faqs',
      MIN_QUESTION_LENGTH: 0,
      MIN_ANSWER_LENGTH:0,
      ANSWER_PREVIEW_LENGTH: 120
    };

    const DOM = {
      tbody: document.getElementById('faqTableBody'),
      emptyState: document.getElementById('emptyState'),
      searchInput: document.getElementById('search'),
      refreshBtn: document.getElementById('refresh'),
      newFaqBtn: document.getElementById('newFaqBtn'),
      formSection: document.getElementById('formSection'),
      formTitle: document.getElementById('formTitle'),
      questionInput: document.getElementById('question'),
      answerInput: document.getElementById('answer'),
      categoryInput: document.getElementById('category'),
      categoryRadios: document.getElementById('categoryRadios'),
      saveFaqBtn: document.getElementById('saveFaq'),
      cancelFormBtn: document.getElementById('cancelForm'),
      cancelForm: document.getElementById('cancelForm'),
      addLinkBtn: document.getElementById('addLinkBtn'),
      formHint: document.getElementById('formHint'),
      statusIndicator: document.getElementById('statusIndicator'),
      editCategoriesBtn: document.getElementById('editCategoriesBtn')
    };

    let STATE = {
      faqs: [],
      editingId: null,
      isLoading: false,
      categories: []
    };

    const CategoryManager = {
      updateFromFaqs() {
        const set = new Set();
        for (const f of STATE.faqs) {
          if (f.category) set.add(f.category);
        }
        STATE.categories = Array.from(set).sort((a,b) => a.localeCompare(b));
        if (!STATE.categories.includes('Umum')) STATE.categories.unshift('Umum');
      },

      renderRadios(selected = null) {
        if (!DOM.categoryRadios) return;
        const radios = STATE.categories.map((c, idx) => {
          const id = `cat_${idx}`;
          return `
            <label>
              <input type="radio" name="kategoriRadio" value="${this.escape(c)}" id="${id}" ${selected===c ? 'checked' : ''}/>
              <span>${this.escape(c)}</span>
            </label>
          `;
        }).join('');
        const otherChecked = (selected && !STATE.categories.includes(selected)) ? 'checked' : '';
        const otherHtml = `
          <label>
            <input type="radio" name="kategoriRadio" value="__other__" id="cat_other" ${otherChecked}/>
            <span>Lain-lain</span>
          </label>
        `;
        DOM.categoryRadios.innerHTML = radios + otherHtml;
        const nodes = DOM.categoryRadios.querySelectorAll('input[name="kategoriRadio"]');
        nodes.forEach(n => n.addEventListener('change', (e) => {
          if (e.target.value === '__other__') {
            DOM.categoryInput.style.display = 'block';
            DOM.categoryInput.focus();
          } else {
            DOM.categoryInput.style.display = 'none';
            DOM.categoryInput.value = '';
          }
        }));
        if (selected && !STATE.categories.includes(selected)) {
          DOM.categoryInput.style.display = 'block';
          DOM.categoryInput.value = selected;
        } else {
          if (DOM.categoryInput) DOM.categoryInput.style.display = 'none';
        }
      },

      addCategory(name) {
        name = (name || '').trim();
        if (!name) return;
        if (!STATE.categories.includes(name)) {
          STATE.categories.push(name);
          STATE.categories.sort((a,b)=>a.localeCompare(b));
        }
        this.renderRadios(name);
      },

      showEditModal() {
        const existing = document.getElementById('categoryModal');
        if (existing) existing.remove();

        const modal = document.createElement('div');
        modal.id = 'categoryModal';
        modal.style = 'position:fixed;inset:0;background:rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;z-index:9999;';
        modal.innerHTML = `
          <div style="width:420px;background:#fff;border-radius:10px;padding:16px;box-shadow:0 10px 30px rgba(0,0,0,0.18);">
            <h3 style="margin:0 0 8px 0;">Urus Kategori</h3>
            <div id="catList" style="max-height:260px;overflow:auto;padding:6px;display:flex;flex-direction:column;gap:8px;"></div>
            <div style="display:flex;gap:8px;margin-top:12px;align-items:center;">
              <input id="newCatInput" placeholder="Kategori baru..." style="flex:1;padding:8px;border:1px solid #e6eef9;border-radius:8px;" />
              <button id="addNewCatBtn" class="btn primary">Tambah</button>
            </div>
            <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px;">
              <button id="closeCatModal" class="btn ghost">Tutup</button>
            </div>
          </div>
        `;
        document.body.appendChild(modal);

        const catList = modal.querySelector('#catList');
        const newCatInput = modal.querySelector('#newCatInput');
        const addNewCatBtn = modal.querySelector('#addNewCatBtn');
        const closeBtn = modal.querySelector('#closeCatModal');

        function renderList() {
          catList.innerHTML = STATE.categories.map((c, idx) => `
            <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px;border:1px solid #f3f6fb;border-radius:8px;">
              <div style="flex:1;">
                <input data-idx="${idx}" class="renameInput" value="${c}" style="width:100%;padding:6px;border:0;background:transparent;font-weight:600" />
              </div>
              <div style="display:flex;gap:6px;">
                <button data-idx="${idx}" class="btn ghost saveRename">Simpan</button>
                <button data-idx="${idx}" class="btn warn deleteCat">Padam</button>
              </div>
            </div>
          `).join('');
          const saveBtns = modal.querySelectorAll('.saveRename');
          saveBtns.forEach(b => b.addEventListener('click', (e)=>{
            const idx = Number(b.getAttribute('data-idx'));
            const input = modal.querySelector(`.renameInput[data-idx="${idx}"]`);
            const newName = (input.value || '').trim();
            if (!newName) { alert('Nama kategori tidak boleh kosong'); return; }
            STATE.categories[idx] = newName;
            STATE.categories = Array.from(new Set(STATE.categories)).sort((a,b)=>a.localeCompare(b));
            renderList();
            CategoryManager.renderRadios();
            updateSidebarStats();
          }));
          const delBtns = modal.querySelectorAll('.deleteCat');
          delBtns.forEach(b => b.addEventListener('click', (e)=>{
            const idx = Number(b.getAttribute('data-idx'));
            const c = STATE.categories[idx];
            if (!confirm(`Padam kategori "${c}"? Semua FAQ yang menggunakan kategori ini akan menjadi kosong.`)) return;
            STATE.categories.splice(idx,1);
            renderList();
            CategoryManager.renderRadios();
            updateSidebarStats();
          }));
        }

        addNewCatBtn.addEventListener('click', () => {
          const val = (newCatInput.value || '').trim();
          if (!val) return;
          if (!STATE.categories.includes(val)) STATE.categories.push(val);
          STATE.categories.sort((a,b)=>a.localeCompare(b));
          newCatInput.value = '';
          renderList();
          CategoryManager.renderRadios();
          updateSidebarStats();
        });

        closeBtn.addEventListener('click', () => modal.remove());

        renderList();
      },

      escape: function(s){ 
        return (s||'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
      }
    };

    const FormManager = {
      reset() {
        STATE.editingId = null;
        DOM.questionInput.value = '';
        DOM.answerInput.value = '';
        DOM.categoryInput.value = '';
        DOM.formHint.textContent = '';
        DOM.formHint.className = 'form-message';
        DOM.formHint.style.display = 'none';
        CategoryManager.renderRadios(null);
      },

      show(isEdit = false, existing = null) {
        DOM.formTitle.textContent = isEdit ? '✏️ Kemaskini FAQ' :  'Tambah FAQ';
        if (isEdit && existing) {
          DOM.questionInput.value = existing.question || '';
          DOM.answerInput.value = existing.answer || '';
          CategoryManager.renderRadios(existing.category || null);
          if (existing.category && !STATE.categories.includes(existing.category)) {
            DOM.categoryInput.style.display = 'block';
            DOM.categoryInput.value = existing.category;
          } else {
            DOM.categoryInput.style.display = 'none';
            DOM.categoryInput.value = '';
          }
          STATE.editingId = existing.id;
        } else {
          CategoryManager.renderRadios(null);
          DOM.categoryInput.style.display = 'none';
          DOM.categoryInput.value = '';
        }
        DOM.formSection.style.display = 'block';
        DOM.formHint.style.display = 'none';
        DOM.questionInput.focus();
      },

      hide() {
        DOM.formSection.style.display = 'none';
        this.reset();
      },

      validate() {
        const question = DOM.questionInput.value.trim();
        const answer = DOM.answerInput.value.trim();

        if (!question) {
          UIManager.showMessage('❌ Sila masukkan soalan.', true);
          DOM.questionInput.focus();
          return false;
        }

        if (!answer) {
          UIManager.showMessage('❌ Sila masukkan jawapan.', true);
          DOM.answerInput.focus();
          return false;
        }

        if (question.length < CONFIG.MIN_QUESTION_LENGTH) {
          UIManager.showMessage(`❌ Soalan terlalu pendek. Sila masukkan sekurang-kurangnya ${CONFIG.MIN_QUESTION_LENGTH} aksara.`, true);
          DOM.questionInput.focus();
          return false;
        }

        if (answer.length < CONFIG.MIN_ANSWER_LENGTH) {
          UIManager.showMessage(`❌ Jawapan terlalu pendek. Sila masukkan sekurang-kurangnya ${CONFIG.MIN_ANSWER_LENGTH} aksara.`, true);
          DOM.answerInput.focus();
          return false;
        }

        return true;
      },

      getFormData() {
        const checked = DOM.formSection.querySelector('input[name="kategoriRadio"]:checked');
        let category = null;
        if (checked) {
          if (checked.value === '__other__') {
            category = DOM.categoryInput.value.trim() || null;
          } else {
            category = checked.value || null;
          }
        } else {
          category = DOM.categoryInput.value.trim() || null;
        }

        return {
          question: DOM.questionInput.value.trim(),
          answer: DOM.answerInput.value.trim(),
          category: category
        };
      }
    };

    const UIManager = {
      showLoading(show = true) {
        STATE.isLoading = show;
        if (DOM.saveFaqBtn) DOM.saveFaqBtn.disabled = show;
        if (DOM.saveFaqBtn) DOM.saveFaqBtn.innerHTML = show ? '⏳ Menyimpan...' : (STATE.editingId ? '💾 Kemaskini' : '💾 Simpan');
        if (DOM.refreshBtn) DOM.refreshBtn.disabled = show;
        if (DOM.refreshBtn) DOM.refreshBtn.innerHTML = show ? '⏳ Memuat...' : '🔄 Refresh';
      },

      updateStatus(message, isError = false) {
        if (DOM.statusIndicator) {
          DOM.statusIndicator.textContent = message;
          DOM.statusIndicator.style.color = isError ? '#e53e3e' : '#718096';
        }
      },

      showMessage(message, isError = false) {
        if (DOM.formHint) {
          DOM.formHint.textContent = message;
          DOM.formHint.className = 'form-message ' + (isError ? 'error' : 'success');
          DOM.formHint.style.display = 'block';
        }
      },

      escapeHtml(str) {
        return (str || '')
          .replaceAll('&', '&amp;')
          .replaceAll('<', '&lt;')
          .replaceAll('>', '&gt;');
      },

      renderRows(items) {
        if (!DOM.tbody) return;
        DOM.tbody.innerHTML = items.map(f => `
          <tr>
            <td><span class="id-badge">#${f.id}</span></td>
            <td>
              <div style="max-width: 500px;">
                <div class="question-text">${this.escapeHtml(f.question)}</div>
                <div class="answer-preview">
                  ${this.escapeHtml(f.answer || '').substring(0, CONFIG.ANSWER_PREVIEW_LENGTH)}${f.answer && f.answer.length > CONFIG.ANSWER_PREVIEW_LENGTH ? '...' : ''}
                </div>
              </div>
            </td>
            <td>
              <span class="category-badge">
                ${this.escapeHtml(f.category || 'Umum')}
              </span>
            </td>
            <td>
              <div class="admin-actions">
                <button class="btn ghost" data-action="edit" data-id="${f.id}" title="Edit FAQ">✏️ Edit</button>
                <button class="btn warn" data-action="delete" data-id="${f.id}" title="Padam FAQ">🗑️ Padam</button>
              </div>
            </td>
          </tr>
        `).join('');
        if (DOM.emptyState) DOM.emptyState.style.display = items.length ? 'none' : 'block';
      }
    };

    const APIService = {
      async fetchFaqs() {
        const res = await fetch(CONFIG.API_BASE);
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        const data = await res.json();
        return data.faqs || [];
      },
      async createFaq(payload) {
        const res = await fetch(CONFIG.API_BASE, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`);
        }
        return await res.json();
      },
      async updateFaq(id, payload) {
        const res = await fetch(`${CONFIG.API_BASE}/${id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`);
        }
        return await res.json();
      },
      async deleteFaq(id) {
        const res = await fetch(`${CONFIG.API_BASE}/${id}`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' }
        });
        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`);
        }
        return await res.json();
      }
    };

    const FAQOperations = {
      async load() {
        try {
          UIManager.showLoading(true);
          UIManager.updateStatus('⏳ Memuat FAQ...');
          STATE.faqs = await APIService.fetchFaqs();
          CategoryManager.updateFromFaqs();
          CategoryManager.renderRadios();
          SearchManager.apply();
          
          // Update sidebar stats
          updateSidebarStats();
          
          if (STATE.faqs.length === 0) {
            UIManager.updateStatus('📝 Tiada FAQ ditemui. Klik "Soalan Baharu" untuk menambah FAQ pertama.');
          } else {
            UIManager.updateStatus(`✅ ${STATE.faqs.length} FAQ ditemui`);
          }
        } catch (error) {
          console.error('Error loading FAQs:', error);
          UIManager.updateStatus(`❌ Gagal memuat FAQ: ${error.message}`, true);
          STATE.faqs = [];
          SearchManager.apply();
        } finally {
          UIManager.showLoading(false);
        }
      },

      async save() {
        if (STATE.isLoading || !FormManager.validate()) return;
        const formData = FormManager.getFormData();
        try {
          UIManager.showLoading(true);
          UIManager.showMessage('⏳ Menyimpan FAQ...', false);
          if (STATE.editingId) {
            await APIService.updateFaq(STATE.editingId, formData);
            UIManager.showMessage('✅ FAQ berjaya dikemaskini!', false);
          } else {
            await APIService.createFaq(formData);
            UIManager.showMessage('✅ FAQ berjaya ditambah!', false);
          }
          await this.load();
          setTimeout(() => FormManager.hide(), 1500);
        } catch (error) {
          console.error('Save error:', error);
          UIManager.showMessage(`❌ Gagal menyimpan: ${error.message}`, true);
        } finally {
          UIManager.showLoading(false);
        }
      },

      async delete(id, question) {
        const confirmed = confirm(
          `⚠️ Adakah anda pasti mahu memadam FAQ berikut?\n\n"${question}"\n\nTindakan ini tidak boleh dibatalkan.`
        );
        if (!confirmed) return;
        try {
          UIManager.showLoading(true);
          UIManager.updateStatus('⏳ Memadam FAQ...');
          const result = await APIService.deleteFaq(id);
          if (result.deleted) {
            UIManager.updateStatus('✅ FAQ berjaya dipadam!');
            await this.load();
          } else {
            throw new Error('Gagal memadam FAQ');
          }
        } catch (error) {
          console.error('Delete error:', error);
          UIManager.updateStatus(`❌ Gagal memadam: ${error.message}`, true);
        } finally {
          UIManager.showLoading(false);
        }
      }
    };

    const SearchManager = {
      apply() {
        const query = (DOM.searchInput?.value || '').toLowerCase().trim();
        if (!query) {
          UIManager.renderRows(STATE.faqs);
          return;
        }
        const filtered = STATE.faqs.filter(f =>
          (f.question && f.question.toLowerCase().includes(query)) ||
          (f.answer && f.answer.toLowerCase().includes(query)) ||
          (f.category && f.category.toLowerCase().includes(query))
        );
        UIManager.renderRows(filtered);
      }
    };

    // Update sidebar statistics with comprehensive data
    function updateSidebarStats() {
      const totalFaqsEl = document.getElementById('totalFaqs');
      const totalCategoriesEl = document.getElementById('totalCategories');
      const lastUpdatedEl = document.getElementById('lastUpdated');
      const avgAnswerLengthEl = document.getElementById('avgAnswerLength');
      const mostUsedCategoryEl = document.getElementById('mostUsedCategory');
      
      // Basic counts
      if (totalFaqsEl) {
        totalFaqsEl.textContent = STATE.faqs.length;
      }
      
      if (totalCategoriesEl) {
        totalCategoriesEl.textContent = STATE.categories.length;
      }
      
      // Last updated time
      if (lastUpdatedEl) {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('ms-MY', { hour: '2-digit', minute: '2-digit' });
        lastUpdatedEl.textContent = timeStr;
      }
      
      // Average answer length
      if (avgAnswerLengthEl && STATE.faqs.length > 0) {
        const totalLength = STATE.faqs.reduce((sum, faq) => sum + (faq.answer?.length || 0), 0);
        const avgLength = Math.round(totalLength / STATE.faqs.length);
        avgAnswerLengthEl.textContent = `Avg: ${avgLength} chars`;
      } else if (avgAnswerLengthEl) {
        avgAnswerLengthEl.textContent = 'No data';
      }
      
      // Most used category
      if (mostUsedCategoryEl && STATE.faqs.length > 0) {
        const categoryCounts = {};
        STATE.faqs.forEach(faq => {
          const cat = faq.category || 'Uncategorized';
          categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
        });
        
        let maxCategory = '';
        let maxCount = 0;
        Object.entries(categoryCounts).forEach(([cat, count]) => {
          if (count > maxCount) {
            maxCount = count;
            maxCategory = cat;
          }
        });
        
        mostUsedCategoryEl.textContent = `${maxCategory} (${maxCount})`;
      } else if (mostUsedCategoryEl) {
        mostUsedCategoryEl.textContent = 'No data';
      }
      
      // Add animation effect
      [totalFaqsEl, totalCategoriesEl].forEach(el => {
        if (el) {
          el.style.transform = 'scale(1.15)';
          setTimeout(() => {
            el.style.transform = 'scale(1)';
          }, 200);
        }
      });
    }

    // Utility: insert text (HTML) at cursor position in a textarea
    function insertAtCursor(textarea, text) {
      textarea.focus();
      const start = textarea.selectionStart || 0;
      const end = textarea.selectionEnd || 0;
      const before = textarea.value.substring(0, start);
      const after = textarea.value.substring(end);
      textarea.value = before + text + after;
      // place cursor after inserted text
      const caret = before.length + text.length;
      textarea.setSelectionRange(caret, caret);
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Validate and normalize URL (adds http:// when missing)
    function normalizeUrl(url) {
      if (!url) return null;
      url = url.trim();
      if (!/^(https?:\/\/|mailto:|tel:)/i.test(url)) {
        // treat plain www. as http
        if (/^www\./i.test(url)) url = 'http://' + url;
        else url = 'http://' + url;
      }
      // simple sanity check
      if (!/^(https?:\/\/|mailto:|tel:)/i.test(url)) return null;
      return url;
    }

    // Helper function for escaping HTML in links
    function escapeHtmlForLink(str) {
      return (str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    // EventHandlers
    const EventHandlers = {
      init() {
        if (DOM.newFaqBtn) DOM.newFaqBtn.addEventListener('click', () => FormManager.show(false));
        if (DOM.cancelFormBtn) DOM.cancelFormBtn.addEventListener('click', () => FormManager.hide());
        if (DOM.cancelForm) DOM.cancelForm.addEventListener('click', () => FormManager.hide());
        if (DOM.saveFaqBtn) DOM.saveFaqBtn.addEventListener('click', () => FAQOperations.save());
        if (DOM.editCategoriesBtn) DOM.editCategoriesBtn.addEventListener('click', () => CategoryManager.showEditModal());
        
        // Enhanced Add Link Button with Modal
        if (DOM.addLinkBtn && DOM.answerInput) {
          DOM.addLinkBtn.addEventListener('click', () => {
            const modal = document.getElementById('linkModal');
            const linkUrlInput = document.getElementById('linkUrl');
            const linkTextInput = document.getElementById('linkText');
            
            if (modal) {
              modal.style.display = 'flex';
              linkUrlInput.value = '';
              linkTextInput.value = '';
              linkUrlInput.focus();
            }
          });
        }

        // Handle insert link button in modal
        const insertLinkBtn = document.getElementById('insertLinkBtn');
        if (insertLinkBtn) {
          insertLinkBtn.addEventListener('click', () => {
            const linkUrlInput = document.getElementById('linkUrl');
            const linkTextInput = document.getElementById('linkText');
            const url = linkUrlInput.value.trim();
            
            if (!url) {
              alert('Sila masukkan URL');
              return;
            }

            const normalized = normalizeUrl(url);
            if (!normalized) {
              alert('URL tidak sah. Pastikan URL bermula dengan http:// atau https://');
              return;
            }

            const label = linkTextInput.value.trim();
            const display = label || normalized.replace(/^https?:\/\/(www\.)?/i, '').split('/')[0];
            
            // Create HTML anchor tag
            const anchor = `<a href="${normalized}" target="_blank" rel="noopener noreferrer">${escapeHtmlForLink(display)}</a>`;
            
            // Insert into textarea
            insertAtCursor(DOM.answerInput, anchor);
            
            // Close modal
            document.getElementById('linkModal').style.display = 'none';
          });
        }

        // Close modal when clicking overlay
        const linkModal = document.getElementById('linkModal');
        if (linkModal) {
          const overlay = linkModal.querySelector('.modal-overlay');
          if (overlay) {
            overlay.addEventListener('click', () => {
              linkModal.style.display = 'none';
            });
          }
        }

        // Table action handlers
        if (DOM.tbody) {
          DOM.tbody.addEventListener('click', async (e) => {
            const btn = e.target.closest('button');
            if (!btn || STATE.isLoading) return;
            const id = btn.getAttribute('data-id');
            const action = btn.getAttribute('data-action');
            const row = STATE.faqs.find(x => String(x.id) === String(id));
            if (action === 'edit') {
              FormManager.show(true, row);
            } else if (action === 'delete') {
              const question = row?.question || 'FAQ ini';
              FAQOperations.delete(id, question);
            }
          });
        }
        
        if (DOM.searchInput) DOM.searchInput.addEventListener('input', () => SearchManager.apply());
        if (DOM.refreshBtn) DOM.refreshBtn.addEventListener('click', () => FAQOperations.load());
      }
    };

    function init() {
      EventHandlers.init();
      CategoryManager.updateFromFaqs();
      CategoryManager.renderRadios();
      FAQOperations.load();
    }

    // expose some helpers for external use (optional)
    window.AdminAPI = {
      reload: () => FAQOperations.load(),
      showForm: (isEdit, existing) => FormManager.show(isEdit, existing)
    };

    init();
  });
})();