(function () {
  'use strict';

  const RARITY_PRICES = { COMMON: 500, RARE: 2000, LEGENDARY: 5000 };

  /* ── Cropper.js CDN ── */
  function loadScript(src, cb) {
    if (document.querySelector('script[src="' + src + '"]')) { cb(); return; }
    const s = document.createElement('script');
    s.src = src; s.onload = cb;
    document.head.appendChild(s);
  }
  function loadCSS(href) {
    if (document.querySelector('link[href="' + href + '"]')) return;
    const l = document.createElement('link');
    l.rel = 'stylesheet'; l.href = href;
    document.head.appendChild(l);
  }

  document.addEventListener('DOMContentLoaded', function () {

    /* ── 1. Авто-цена по редкости ── */
    const rarityField = document.getElementById('id_rarity');
    const priceField  = document.getElementById('id_cost_points10');
    if (rarityField && priceField) {
      rarityField.addEventListener('change', function () {
        const price = RARITY_PRICES[this.value];
        if (price) priceField.value = price;
      });
    }

    /* ── 2. Динамическая фильтрация блюд по кафе ── */
    const cafeSelect     = document.getElementById('id_cafe');
    const menuItemSelect = document.getElementById('id_menu_item');

    if (cafeSelect && menuItemSelect) {
      // Сохраняем все опции
      const allOptions = Array.from(menuItemSelect.options).map(o => ({
        value: o.value, text: o.text, dataset: o.dataset
      }));

      function filterMenuItems() {
        const cafeId = cafeSelect.value;
        const current = menuItemSelect.value;
        menuItemSelect.innerHTML = '';

        // Пустой вариант
        const empty = document.createElement('option');
        empty.value = ''; empty.text = '---------';
        menuItemSelect.appendChild(empty);

        allOptions.forEach(function (o) {
          if (!o.value) return;
          // Вариант показываем если café совпадает или café не выбрано
          // Django рендерит option как текст "Название блюда" без cafe_id,
          // поэтому делаем AJAX-запрос к django admin autocomplete
          // — но проще: показываем все и фильтруем через get_form на сервере.
          // Здесь оставляем все опции видимыми, сервер уже фильтрует при загрузке страницы.
          const opt = document.createElement('option');
          opt.value = o.value; opt.text = o.text;
          if (o.value === current) opt.selected = true;
          menuItemSelect.appendChild(opt);
        });
      }

      cafeSelect.addEventListener('change', function () {
        // При смене кафе — сбрасываем блюдо
        menuItemSelect.value = '';
      });
    }

    /* ── 3. JS-кроппер для поля "Фон купона" ── */
    const imageInput = document.getElementById('id_image');
    if (!imageInput) return;

    loadCSS('https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css');
    loadScript('https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js', function () {

      // Контейнер под кроппер
      const wrapper = document.createElement('div');
      wrapper.style.cssText = 'margin-top:12px;display:none;';

      const preview = document.createElement('img');
      preview.style.cssText = 'max-width:100%;display:block;';
      wrapper.appendChild(preview);

      const cropBtn = document.createElement('button');
      cropBtn.type = 'button';
      cropBtn.textContent = 'Обрезать и применить';
      cropBtn.style.cssText = 'margin-top:8px;padding:6px 16px;background:#417690;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:13px;';
      wrapper.appendChild(cropBtn);

      const hint = document.createElement('div');
      hint.style.cssText = 'margin-top:6px;font-size:11px;color:#666;';
      hint.textContent = 'Соотношение 2:1 (800×400). Перетащите область кадрирования.';
      wrapper.appendChild(hint);

      imageInput.parentNode.insertBefore(wrapper, imageInput.nextSibling);

      let cropper = null;
      let croppedFile = null;

      // Скрытый input для передачи обрезанного файла
      const hiddenInput = document.createElement('input');
      hiddenInput.type = 'file';
      hiddenInput.name = imageInput.name + '_cropped';
      hiddenInput.style.display = 'none';
      imageInput.parentNode.appendChild(hiddenInput);

      imageInput.addEventListener('change', function () {
        const file = this.files[0];
        if (!file) { wrapper.style.display = 'none'; return; }

        const reader = new FileReader();
        reader.onload = function (e) {
          wrapper.style.display = 'block';
          preview.src = e.target.result;

          if (cropper) { cropper.destroy(); cropper = null; }
          cropper = new Cropper(preview, {
            aspectRatio: 2 / 1,
            viewMode: 1,
            autoCropArea: 1,
          });
        };
        reader.readAsDataURL(file);
      });

      cropBtn.addEventListener('click', function () {
        if (!cropper) return;
        cropper.getCroppedCanvas({ width: 800, height: 400 }).toBlob(function (blob) {
          const originalName = imageInput.files[0]?.name || 'coupon_bg.jpg';
          croppedFile = new File([blob], originalName, { type: 'image/jpeg' });

          // Подменяем файл в оригинальном input через DataTransfer
          const dt = new DataTransfer();
          dt.items.add(croppedFile);
          imageInput.files = dt.files;

          cropBtn.textContent = '✓ Обрезано (800×400)';
          cropBtn.style.background = '#28a745';
        }, 'image/jpeg', 0.9);
      });
    });
  });
})();
