/* ==========================================================================
   LÓGICA DE LA APLICACIÓN DE LECTURA - EL CÓDIGO DE PROMETEO
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // --- ESTADO INICIAL ---
    let currentChapterIndex = 0; // 0-based index for NOVEL_DATA.chapters
    let currentEdition = localStorage.getItem('prometheus_edition') || 'hard'; // 'hard' | 'scifi' | 'juvenil'
    let readStatus = JSON.parse(localStorage.getItem('prometheus_read_status')) || {};
    let bookmark = JSON.parse(localStorage.getItem('prometheus_bookmark')) || null;
    let audioContext = null;
    let ambientGain = null;
    let isAudioPlaying = false;

    // --- ELEMENTOS DEL DOM ---
    const progressBar = document.getElementById('progress-bar');
    const headerChapterIndicator = document.getElementById('header-chapter-indicator');
    
    // Sidebar
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const sidebarChaptersList = document.getElementById('sidebar-chapters-list');
    const sidebarFilter = document.getElementById('sidebar-filter');
    const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
    const btnCloseSidebar = document.getElementById('btn-close-sidebar');

    // Canvas de Lectura
    const chapterActBadge = document.getElementById('chapter-act-badge');
    const chapterMainTitle = document.getElementById('chapter-main-title');
    const metaPov = document.getElementById('meta-pov');
    const metaLocation = document.getElementById('meta-location');
    const metaReadtime = document.getElementById('meta-readtime');
    const metaPages = document.getElementById('meta-pages');
    const sceneFicheContent = document.getElementById('scene-fiche-content');
    const chapterBodyContent = document.getElementById('chapter-body-content');

    // Pantalla de Portada y Selector
    const coverLandingView = document.getElementById('cover-landing-view');
    const readerCanvas = document.getElementById('reader-canvas');
    const coverResumeBox = document.getElementById('cover-resume-box');
    const btnCoverResume = document.getElementById('btn-cover-resume');
    const coverResumeChapTitle = document.getElementById('cover-resume-chap-title');
    const coverResumeEditionName = document.getElementById('cover-resume-edition-name');
    const brandHomeLink = document.getElementById('brand-home-link');
    const sidebarCoverLink = document.getElementById('sidebar-cover-link');
    const btnSidebarCover = document.getElementById('btn-sidebar-cover');

    // Botones de Navegación
    const btnPrevChapter = document.getElementById('btn-prev-chapter');
    const btnNextChapter = document.getElementById('btn-next-chapter');
    const prevChapterTitle = document.getElementById('prev-chapter-title');
    const nextChapterTitle = document.getElementById('next-chapter-title');
    const btnBookmark = document.getElementById('btn-bookmark');
    const bookmarkText = document.getElementById('bookmark-text');
    const btnScrollTop = document.getElementById('btn-scroll-top');

    // Modales y Botones
    const btnOpenSettings = document.getElementById('btn-open-settings');
    const btnOpenCodex = document.getElementById('btn-open-codex');
    const btnOpenEscaleta = document.getElementById('btn-open-escaleta');
    const btnOpenGenesis = document.getElementById('btn-open-genesis');
    const btnCloseGenesis = document.getElementById('btn-close-genesis');
    const btnOpenSearch = document.getElementById('btn-open-search');
    const btnOpenAudiobook = document.getElementById('btn-open-audiobook');
    const btnListenChapter = document.getElementById('btn-listen-chapter');
    const btnToggleFocus = document.getElementById('btn-toggle-focus');
    const btnToggleAudio = document.getElementById('btn-toggle-audio');

    // Elementos del Reproductor de Audiolibro
    const abTrackSelect = document.getElementById('ab-track-select');
    const abOptgroupChapters = document.getElementById('ab-optgroup-chapters');
    const abOptgroupBios = document.getElementById('ab-optgroup-bios');
    const abSourceMode = document.getElementById('ab-source-mode');
    const abVocalProfile = document.getElementById('ab-vocal-profile');
    const abSoundscapePreset = document.getElementById('ab-soundscape-preset');
    const abVoiceSelect = document.getElementById('ab-voice-select');
    const abSpeedSelect = document.getElementById('ab-speed-select');
    const abAmbientVol = document.getElementById('ab-ambient-vol');
    const abBtnPlay = document.getElementById('ab-btn-play');
    const abPlayIcon = document.getElementById('ab-play-icon');
    const abBtnPrev = document.getElementById('ab-btn-prev');
    const abBtnNext = document.getElementById('ab-btn-next');
    const abBtnRewind = document.getElementById('ab-btn-rewind');
    const abBtnForward = document.getElementById('ab-btn-forward');
    const abCoverImg = document.getElementById('ab-cover-img');
    const abEqualizer = document.getElementById('ab-equalizer');
    const abTrackTitle = document.getElementById('ab-track-title');
    const abTrackMeta = document.getElementById('ab-track-meta');
    const abCurrentTime = document.getElementById('ab-current-time');
    const abStatusText = document.getElementById('ab-status-text');
    const abProgressBar = document.getElementById('ab-progress-bar');
    const abProgressContainer = document.getElementById('ab-progress-container');
    const abTranscriptBody = document.getElementById('ab-transcript-body');

    // Estado del Audiolibro
    let abCurrentTrackType = 'chapter'; // 'chapter' | 'bio'
    let abCurrentTrackIndex = 0;
    let abParagraphs = [];
    let abActiveParagraphIndex = 0;
    let abIsPlaying = false;
    let abSpeechSynth = window.speechSynthesis;
    let abCurrentUtterance = null;
    let abVoices = [];
    let abParsedBios = [];

    // Elementos de Modales
    const codexContentRendered = document.getElementById('codex-content-rendered');
    const escaletaContentRendered = document.getElementById('escaleta-content-rendered');
    const genesisContentRendered = document.getElementById('genesis-content');
    const globalSearchInput = document.getElementById('global-search-input');
    const searchResultsList = document.getElementById('search-results-list');
    let isProgressBarUpdating = false;

    // Controles de Ajustes
    const sliderFontSize = document.getElementById('slider-font-size');
    const sliderLineHeight = document.getElementById('slider-line-height');
    const sliderTextWidth = document.getElementById('slider-text-width');
    const valFontSize = document.getElementById('val-font-size');
    const valLineHeight = document.getElementById('val-line-height');
    const valTextWidth = document.getElementById('val-text-width');

    // --- INICIALIZACIÓN ---
    initApp();

    function initApp() {
        try { loadPreferences(); } catch(e) { console.error('Error in loadPreferences:', e); }
        if (typeof NOVEL_DATA !== 'undefined') {
            document.title = `${NOVEL_DATA.title} | Novela Interactiva`;
            const bTitle = document.querySelector('.brand-title');
            const bSub = document.querySelector('.brand-subtitle');
            const sbTitle = document.querySelector('.sidebar-info h3');
            const sbStats = document.getElementById('sidebar-stats-text');
            const sbAuthor = document.querySelector('.sidebar-author');
            if (bTitle && NOVEL_DATA.title) bTitle.textContent = NOVEL_DATA.title;
            if (bSub) {
                if (NOVEL_DATA.subtitle && NOVEL_DATA.subtitle.trim()) {
                    bSub.textContent = NOVEL_DATA.subtitle.toUpperCase();
                } else {
                    bSub.style.display = 'none';
                }
            }
            if (sbTitle && NOVEL_DATA.title) sbTitle.textContent = NOVEL_DATA.title;
            if (sbAuthor) {
                const authorName = NOVEL_DATA.author || NOVEL_DATA.director || 'Pedro Garat + Antigravity';
                sbAuthor.innerHTML = `Autor: <strong>${authorName}</strong>`;
            }
            if (sbStats && NOVEL_DATA.totalChapters) {
                sbStats.innerHTML = `${NOVEL_DATA.totalChapters} Capítulos &bull; ~${NOVEL_DATA.totalPages} Páginas &bull; ${NOVEL_DATA.totalWords.toLocaleString()} Palabras`;
            }

            // Sello de Fecha y Hora de Compilación
            if (NOVEL_DATA.lastUpdated) {
                const brandLastUpdated = document.getElementById('brand-last-updated');
                const sidebarLastUpdated = document.getElementById('sidebar-last-updated');
                const readerLastUpdated = document.getElementById('reader-last-updated');
                if (brandLastUpdated) brandLastUpdated.textContent = `Actualizado: ${NOVEL_DATA.lastUpdated}`;
                if (sidebarLastUpdated) sidebarLastUpdated.textContent = NOVEL_DATA.lastUpdated;
                if (readerLastUpdated) readerLastUpdated.textContent = NOVEL_DATA.lastUpdated;
            }
        }
        try { renderSidebarList(); } catch(e) { console.error('Error in renderSidebarList:', e); }
        try { renderCodexAndEscaleta(); } catch(e) { console.error('Error in renderCodexAndEscaleta:', e); }
        try { initAudiobook(); } catch(e) { console.error('Error in initAudiobook:', e); }

        // Inicializar capítulo en memoria
        try {
            if (bookmark && bookmark.chapterIndex !== undefined && bookmark.chapterIndex >= 0 && bookmark.chapterIndex < NOVEL_DATA.chapters.length) {
                currentChapterIndex = bookmark.chapterIndex;
            } else {
                currentChapterIndex = 0;
            }
        } catch(e) {
            currentChapterIndex = 0;
        }

        // Comprobar si se accede con un hash directo a un capítulo (ej: #cap-3)
        let initialChapter = null;
        if (window.location.hash) {
            const m = window.location.hash.match(/^#cap-(\d+)$/);
            if (m) {
                const targetId = parseInt(m[1], 10);
                const foundIdx = NOVEL_DATA.chapters.findIndex(c => c.id === targetId);
                if (foundIdx !== -1) initialChapter = foundIdx;
            }
        }

        if (initialChapter !== null) {
            loadChapter(initialChapter);
        } else {
            // Al entrar en la web sin hash específico, mostrar la Portada y las tres versiones
            try {
                showCoverView();
            } catch(e) {
                console.error('Error showing cover view, falling back to chapter 0:', e);
                loadChapter(0);
            }
        }

        try { setupEventListeners(); } catch(e) { console.error('Error in setupEventListeners:', e); }
        try { updateProgressBar(); } catch(e) { console.error('Error in updateProgressBar:', e); }
        try { checkForRemoteUpdates(); } catch(e) { console.error('Error in checkForRemoteUpdates:', e); }
    }

    // --- MANEJADOR DE EVENTOS GENERAL ---
    function setupEventListeners() {
        // Eventos de Navegación entre capítulos
        btnPrevChapter.addEventListener('click', () => {
            if (currentChapterIndex > 0) loadChapter(currentChapterIndex - 1);
        });

        btnNextChapter.addEventListener('click', () => {
            if (currentChapterIndex < NOVEL_DATA.chapters.length - 1) loadChapter(currentChapterIndex + 1);
        });

        // Sidebar
        btnToggleSidebar.addEventListener('click', openSidebar);
        btnCloseSidebar.addEventListener('click', closeSidebar);
        sidebarOverlay.addEventListener('click', closeSidebar);
        sidebarFilter.addEventListener('input', renderSidebarList);

        // Modales
        if (btnOpenSettings) btnOpenSettings.addEventListener('click', () => openModal('modal-settings'));
        if (btnOpenCodex) btnOpenCodex.addEventListener('click', () => openModal('modal-codex'));
        if (btnOpenEscaleta) btnOpenEscaleta.addEventListener('click', () => openModal('modal-escaleta'));
        if (btnOpenGenesis) btnOpenGenesis.addEventListener('click', () => openModal('modal-genesis'));
        if (btnCloseGenesis) btnCloseGenesis.addEventListener('click', () => closeModal('modal-genesis'));
        if (btnOpenSearch) {
            btnOpenSearch.addEventListener('click', () => {
                openModal('modal-search');
                if (globalSearchInput) globalSearchInput.focus();
            });
        }
        if (btnOpenAudiobook) {
            btnOpenAudiobook.addEventListener('click', () => openAudiobookModal('chapter', currentChapterIndex));
        }
        if (btnListenChapter) {
            btnListenChapter.addEventListener('click', () => {
                openAudiobookModal('chapter', currentChapterIndex);
                playAudiobook();
            });
        }

        // Formulario de Comentarios Nativos
        const commentForm = document.getElementById('comment-publish-form');
        if (commentForm) {
            commentForm.addEventListener('submit', (e) => {
                e.preventDefault();
                publishChapterComment();
            });
        }

        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.classList.add('hidden');
            });
        });

        // Selector de Edición / Tipo de Narrativa (Hard / Sci-Fi / Juvenil)
        document.querySelectorAll('.narrative-opt-btn').forEach(btn => {
            btn.addEventListener('click', () => setEdition(btn.getAttribute('data-edition')));
        });

        // Eventos de la Pantalla de Portada (Tres Versiones)
        document.querySelectorAll('.edition-card-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const ed = btn.getAttribute('data-edition') || 'hard';
                selectNovelEditionAndStart(ed);
            });
        });

        // Delegación de eventos para tarjetas de edición y reanudación
        document.addEventListener('click', (e) => {
            const cardBtn = e.target.closest('.edition-card-btn');
            if (cardBtn) {
                e.preventDefault();
                const ed = cardBtn.getAttribute('data-edition') || 'hard';
                selectNovelEditionAndStart(ed);
                return;
            }
            const resumeBtn = e.target.closest('#btn-cover-resume');
            if (resumeBtn) {
                e.preventDefault();
                resumeSavedReading();
                return;
            }
        });

        if (btnCoverResume) {
            btnCoverResume.addEventListener('click', (e) => {
                e.preventDefault();
                resumeSavedReading();
            });
        }

        // Navegación hacia la Portada desde Header y Sidebar
        if (brandHomeLink) {
            brandHomeLink.addEventListener('click', (e) => {
                if (e.target.closest('#btn-header-refresh') || e.target.id === 'brand-last-updated') return;
                showCoverView();
            });
        }
        if (sidebarCoverLink) {
            sidebarCoverLink.addEventListener('click', () => {
                closeSidebar();
                showCoverView();
            });
        }
        if (btnSidebarCover) {
            btnSidebarCover.addEventListener('click', () => {
                closeSidebar();
                showCoverView();
            });
        }

        document.querySelectorAll('.narrative-setting-btn').forEach(btn => {
            btn.addEventListener('click', () => setEdition(btn.getAttribute('data-edition')));
        });

        const bannerEditionPill = document.getElementById('banner-edition-pill');
        if (bannerEditionPill) {
            bannerEditionPill.addEventListener('click', () => {
                const editions = ['hard', 'scifi', 'juvenil'];
                const nextIdx = (editions.indexOf(currentEdition) + 1) % editions.length;
                setEdition(editions[nextIdx]);
            });
        }

        // Temas y Fuentes
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', () => setTheme(btn.getAttribute('data-theme')));
        });

        document.querySelectorAll('.font-btn').forEach(btn => {
            btn.addEventListener('click', () => setFont(btn.getAttribute('data-font')));
        });

        // Sliders
        if (sliderFontSize) sliderFontSize.addEventListener('input', (e) => setFontSize(e.target.value));
        if (sliderLineHeight) sliderLineHeight.addEventListener('input', (e) => setLineHeight(e.target.value));
        if (sliderTextWidth) sliderTextWidth.addEventListener('input', (e) => setTextWidth(e.target.value));

        // Enfoque y Audio
        if (btnToggleFocus) btnToggleFocus.addEventListener('click', toggleFocusMode);
        if (btnToggleAudio) btnToggleAudio.addEventListener('click', toggleAmbientSound);

        // Marcador y Scroll Top
        if (btnBookmark) btnBookmark.addEventListener('click', saveBookmark);
        if (btnScrollTop) btnScrollTop.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        // Buscador
        if (globalSearchInput) globalSearchInput.addEventListener('input', handleGlobalSearch);

        // Scroll y Redimensionamiento
        window.addEventListener('scroll', updateProgressBar, { passive: true });
        window.addEventListener('resize', updateProgressBar, { passive: true });

        // Atajos de teclado
        document.addEventListener('keydown', handleKeyboardShortcuts);

        // Botones de Forzar Recarga Anti-Caché en Móviles
        const btnHeaderRefresh = document.getElementById('btn-header-refresh');
        const brandLastUpdated = document.getElementById('brand-last-updated');
        const btnSidebarRefresh = document.getElementById('btn-sidebar-refresh');
        const btnFooterRefresh = document.getElementById('btn-footer-refresh');

        [btnHeaderRefresh, brandLastUpdated, btnSidebarRefresh, btnFooterRefresh].forEach(btn => {
            if (btn) {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    forceRefreshCache();
                });
            }
        });

        // Detectar cuando el usuario vuelve a la pestaña en el móvil
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                checkForRemoteUpdates();
            }
        });
        window.addEventListener('focus', checkForRemoteUpdates);
    }

    // --- CONTROL DE ACTUALIZACIÓN ANTI-CACHÉ EN MÓVILES ---
    function forceRefreshCache() {
        const cleanUrl = window.location.origin + window.location.pathname + '?refresh=' + Date.now();
        window.location.href = cleanUrl;
    }

    function checkForRemoteUpdates() {
        try {
            fetch('version.json?t=' + Date.now(), { cache: 'no-store' })
                .then(res => {
                    if (!res.ok) return null;
                    return res.json();
                })
                .then(data => {
                    if (!data || !data.buildTimestamp) return;
                    const localBuild = NOVEL_DATA.buildTimestamp ? new Date(NOVEL_DATA.buildTimestamp).getTime() : 0;
                    const remoteBuild = new Date(data.buildTimestamp).getTime();
                    // Si el servidor tiene una versión más nueva por al menos 5 segundos
                    if (remoteBuild > localBuild + 5000) {
                        showUpdateToast(data.lastUpdated);
                    }
                })
                .catch(() => {});
        } catch(e) {}
    }

    function showUpdateToast(lastUpdatedText) {
        if (document.getElementById('update-notification-toast')) return;
        const toast = document.createElement('div');
        toast.id = 'update-notification-toast';
        toast.className = 'update-notification-toast';
        toast.innerHTML = `
            <span>🚀 <strong>Texto actualizado disponible</strong> (${lastUpdatedText || 'Nueva versión'})</span>
            <button id="btn-toast-reload">Actualizar ahora</button>
        `;
        document.body.appendChild(toast);
        const reloadBtn = document.getElementById('btn-toast-reload');
        if (reloadBtn) reloadBtn.addEventListener('click', forceRefreshCache);
    }

    // Desregistrar cualquier service worker residual
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(registrations => {
            for (let r of registrations) r.unregister();
        }).catch(() => {});
    }

    // --- CARGA DE PREFERENCIAS ---
    function loadPreferences() {
        const theme = localStorage.getItem('prometheus_theme') || 'obsidian';
        const font = localStorage.getItem('prometheus_font') || 'sans';
        const fontSize = localStorage.getItem('prometheus_font_size') || '19';
        const lineHeight = localStorage.getItem('prometheus_line_height') || '1.8';
        const textWidth = localStorage.getItem('prometheus_text_width') || '800';
        currentEdition = localStorage.getItem('prometheus_edition') || 'hard';

        setTheme(theme);
        setFont(font);
        setFontSize(fontSize);
        setLineHeight(lineHeight);
        setTextWidth(textWidth);
        setEdition(currentEdition, false);
    }

    function setEdition(edition, reload = true) {
        currentEdition = edition;
        localStorage.setItem('prometheus_edition', edition);

        const editionLabels = {
            'hard': '⚛️ Hard Sci-Fi',
            'scifi': '🚀 Sci-Fi (Narrativa)',
            'juvenil': '⚡ Juvenil / Adolescente'
        };

        const bannerPill = document.getElementById('banner-edition-pill');
        if (bannerPill) {
            bannerPill.textContent = editionLabels[edition] || '⚛️ Hard Sci-Fi';
        }

        // Actualizar botones de la caja inferior
        document.querySelectorAll('.narrative-opt-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-edition') === edition);
        });

        // Actualizar botones en modal de ajustes
        document.querySelectorAll('.narrative-setting-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-edition') === edition);
        });

        // Actualizar botones en pantalla de portada
        document.querySelectorAll('.edition-card-btn').forEach(btn => {
            btn.classList.toggle('selected', btn.getAttribute('data-edition') === edition);
        });

        if (reload && NOVEL_DATA && NOVEL_DATA.chapters && NOVEL_DATA.chapters[currentChapterIndex]) {
            const chap = NOVEL_DATA.chapters[currentChapterIndex];
            let activeContent = chap.content;
            if (currentEdition === 'scifi' && chap.content_scifi) {
                activeContent = chap.content_scifi;
            } else if (currentEdition === 'juvenil' && chap.content_juvenil) {
                activeContent = chap.content_juvenil;
            }
            chapterBodyContent.innerHTML = parseChapterBody(activeContent);
            updateProgressBar();
        }
    }

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('prometheus_theme', theme);
        document.querySelectorAll('.theme-btn').forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-theme') === theme);
        });
    }

    function setFont(font) {
        document.documentElement.setAttribute('data-font', font);
        localStorage.setItem('prometheus_font', font);
        document.querySelectorAll('.font-btn').forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-font') === font);
        });
    }

    function setFontSize(size) {
        document.documentElement.style.setProperty('--reader-font-size', `${size}px`);
        if (valFontSize) valFontSize.textContent = `${size}px`;
        if (sliderFontSize) sliderFontSize.value = size;
        localStorage.setItem('prometheus_font_size', size);
    }

    function setLineHeight(height) {
        document.documentElement.style.setProperty('--reader-line-height', height);
        if (valLineHeight) valLineHeight.textContent = height;
        if (sliderLineHeight) sliderLineHeight.value = height;
        localStorage.setItem('prometheus_line_height', height);
    }

    function setTextWidth(width) {
        document.documentElement.style.setProperty('--reader-max-width', `${width}px`);
        if (valTextWidth) valTextWidth.textContent = `${width}px`;
        if (sliderTextWidth) sliderTextWidth.value = width;
        localStorage.setItem('prometheus_text_width', width);
    }

    // --- CONTROL DE PANTALLA DE PORTADA Y SELECTOR DE VERSIONES ---
    function getEditionDisplayName(ed) {
        switch (ed) {
            case 'scifi': return 'Sci-Fi (Narrativa)';
            case 'juvenil': return 'Juvenil / Adolescente';
            default: return 'Hard Sci-Fi';
        }
    }

    function selectNovelEditionAndStart(ed) {
        if (!ed) ed = 'hard';
        setEdition(ed, false);
        const targetChapter = (bookmark && typeof bookmark.chapterIndex === 'number' && bookmark.chapterIndex >= 0 && bookmark.chapterIndex < NOVEL_DATA.chapters.length) 
            ? bookmark.chapterIndex 
            : 0;
        const targetScroll = (bookmark && bookmark.chapterIndex === targetChapter) ? (bookmark.scrollTop || 0) : 0;
        showReaderView(targetChapter, targetScroll);
    }

    function resumeSavedReading() {
        const targetChapter = (bookmark && typeof bookmark.chapterIndex === 'number' && bookmark.chapterIndex >= 0 && bookmark.chapterIndex < NOVEL_DATA.chapters.length) 
            ? bookmark.chapterIndex 
            : 0;
        const targetScroll = (bookmark && bookmark.chapterIndex === targetChapter) ? (bookmark.scrollTop || 0) : 0;
        showReaderView(targetChapter, targetScroll);
    }

    window.selectNovelEditionAndStart = selectNovelEditionAndStart;
    window.resumeSavedReading = resumeSavedReading;
    window.showCoverLanding = showCoverView;

    function filterCharacterCards(category) {
        document.querySelectorAll('.char-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-category') === category);
        });
        document.querySelectorAll('.char-card').forEach(card => {
            if (category === 'all' || card.getAttribute('data-category') === category) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
    }
    window.filterCharacterCards = filterCharacterCards;

    function showCoverView() {
        if (coverLandingView) coverLandingView.style.display = 'block';
        if (readerCanvas) readerCanvas.style.display = 'none';
        if (headerChapterIndicator) headerChapterIndicator.textContent = 'Portada • 3 Ediciones';
        if (progressBar) progressBar.style.width = '0%';

        // Mostrar u ocultar la opción de reanudar lectura si hay marcador
        if (coverResumeBox) {
            if (bookmark && bookmark.chapterIndex !== undefined && bookmark.chapterIndex >= 0 && bookmark.chapterIndex < NOVEL_DATA.chapters.length) {
                const chap = NOVEL_DATA.chapters[bookmark.chapterIndex];
                if (coverResumeChapTitle) coverResumeChapTitle.textContent = chap.title || `Capítulo ${bookmark.chapterIndex + 1}`;
                if (coverResumeEditionName) coverResumeEditionName.textContent = getEditionDisplayName(currentEdition);
                coverResumeBox.style.display = 'flex';
            } else {
                coverResumeBox.style.display = 'none';
            }
        }

        // Marcar la tarjeta seleccionada
        document.querySelectorAll('.edition-card-btn').forEach(btn => {
            btn.classList.toggle('selected', btn.getAttribute('data-edition') === currentEdition);
        });

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function showReaderView(chapterIdx, scrollPos) {
        if (coverLandingView) coverLandingView.style.display = 'none';
        if (readerCanvas) readerCanvas.style.display = 'block';
        const targetIdx = (chapterIdx !== undefined && chapterIdx >= 0) ? chapterIdx : currentChapterIndex;
        loadChapter(targetIdx, scrollPos || 0);
    }

    // --- CARGAR Y RENDERIZAR CAPÍTULO ---
    function loadChapter(index, scrollToPosition = 0) {
        if (index < 0 || index >= NOVEL_DATA.chapters.length) return;

        // Asegurar que el canvas de lectura esté visible y la portada oculta
        if (coverLandingView) coverLandingView.style.display = 'none';
        if (readerCanvas) readerCanvas.style.display = 'block';

        currentChapterIndex = index;
        const chap = NOVEL_DATA.chapters[index];

        // Actualizar UI del Encabezado y Viñeta
        const chapterVignetteImg = document.getElementById('chapter-vignette-img');
        if (chapterVignetteImg && chap.povImage) {
            chapterVignetteImg.src = chap.povImage;
            chapterVignetteImg.alt = `Retrato POV: ${chap.pov}`;
        }

        chapterActBadge.textContent = chap.act;
        chapterMainTitle.textContent = chap.title.startsWith('Capítulo') ? chap.title : `Capítulo ${chap.id}: ${chap.title}`;
        metaPov.textContent = `👁️ POV: ${chap.pov}`;
        metaLocation.textContent = `📍 ${chap.location}`;
        metaReadtime.textContent = `⏱️ ${chap.readTime}`;
        metaPages.textContent = `📄 ~${chap.pages} páginas`;
        headerChapterIndicator.textContent = `Capítulo ${chap.id} de ${NOVEL_DATA.totalChapters}`;

        // Ficha de la escena (desglose)
        if (chap.desglose) {
            sceneFicheContent.innerHTML = renderMarkdown(chap.desglose);
        } else {
            sceneFicheContent.innerHTML = '<p>Ficha de escena nominal.</p>';
        }

        // Renderizar el cuerpo del texto según la edición de narrativa activa
        let activeContent = chap.content;
        if (currentEdition === 'scifi' && chap.content_scifi) {
            activeContent = chap.content_scifi;
        } else if (currentEdition === 'juvenil' && chap.content_juvenil) {
            activeContent = chap.content_juvenil;
        }
        chapterBodyContent.innerHTML = parseChapterBody(activeContent);
        setEdition(currentEdition, false);

        // Actualizar botones de navegación
        updateNavButtons();

        // Actualizar marcador visual
        updateBookmarkState();

        // Actualizar lista en sidebar
        renderSidebarList();

        // Desplazar vista al inicio o posición guardada
        if (scrollToPosition > 0) {
            window.scrollTo({ top: scrollToPosition, behavior: 'smooth' });
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        updateProgressBar();
        setTimeout(updateProgressBar, 150);

        // Guardar progreso automático
        readStatus[chap.id] = true;
        localStorage.setItem('prometheus_read_status', JSON.stringify(readStatus));

        // Actualizar sección de comentarios (Cusdis)
        updateChapterComments(chap);

        // Actualizar URL y hash para Cloudflare Analytics (medición por capítulo en SPA)
        try {
            const chapHash = `#cap-${chap.id}`;
            if (window.location.hash !== chapHash) {
                history.replaceState({ chapterIndex: index }, chap.title, chapHash);
            }
        } catch(e) {}

        closeSidebar();
    }

    // --- SISTEMA NATIVO DE COMENTARIOS (FIREBASE FIRESTORE) ---
    const firebaseConfig = {
        apiKey: "AIzaSyBpbOxU7zo_3_kmvUElNyalYv_qYu7Dc3U",
        authDomain: "sombra-novela.firebaseapp.com",
        projectId: "sombra-novela",
        storageBucket: "sombra-novela.firebasestorage.app",
        messagingSenderId: "345722094648",
        appId: "1:345722094648:web:21f9b1bc6da39e9dddd2cd"
    };

    let firestoreDb = null;
    function getFirestoreDb() {
        if (!firestoreDb && typeof firebase !== 'undefined') {
            try {
                if (!firebase.apps.length) {
                    firebase.initializeApp(firebaseConfig);
                }
                firestoreDb = firebase.firestore();
            } catch(e) {
                console.warn('Error inicializando Firestore:', e);
            }
        }
        return firestoreDb;
    }

    function escapeCommentHtml(str) {
        if (!str) return '';
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function formatCommentTimestamp(timestamp) {
        if (!timestamp) return 'Reciente';
        const d = new Date(timestamp);
        const now = new Date();
        const diffSeconds = Math.floor((now - d) / 1000);
        if (diffSeconds < 60) return 'Hace un instante';
        if (diffSeconds < 3600) return `Hace ${Math.floor(diffSeconds / 60)} min`;
        if (diffSeconds < 86400) return `Hace ${Math.floor(diffSeconds / 3600)} h`;
        if (diffSeconds < 86400 * 7) return `Hace ${Math.floor(diffSeconds / 86400)} días`;
        return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });
    }

    function updateChapterComments(chap) {
        const commentsLabel = document.getElementById('comments-chapter-label');
        const authorInput = document.getElementById('comment-author-input');
        if (commentsLabel) {
            const chapTitle = chap.title.startsWith('Capítulo') ? chap.title : `Capítulo ${chap.id}: ${chap.title}`;
            commentsLabel.textContent = `Comparte tus impresiones, teorías y reflexiones sobre ${chapTitle}`;
        }

        // Cargar nombre recordado en localStorage
        if (authorInput) {
            const savedName = localStorage.getItem('sombra_commenter_name');
            if (savedName && !authorInput.value) {
                authorInput.value = savedName;
            }
        }

        // Cargar comentarios del capítulo
        fetchChapterComments(chap.id);
    }

    function fetchChapterComments(chapterId) {
        const container = document.getElementById('comments-list-container');
        const countBadge = document.getElementById('comments-count-badge');
        if (!container) return;

        container.innerHTML = '<div class="comments-empty-state">Cargando comentarios...</div>';

        const db = getFirestoreDb();
        if (!db) {
            container.innerHTML = '<div class="comments-empty-state">💬 Escribe el primer comentario sobre este capítulo.</div>';
            return;
        }

        db.collection('comments')
            .where('chapter_id', '==', chapterId)
            .get()
            .then(snapshot => {
                if (snapshot.empty) {
                    if (countBadge) countBadge.textContent = '0';
                    container.innerHTML = `
                        <div class="comments-empty-state">
                            💬 Aún no hay comentarios en este capítulo.<br>
                            <span style="font-size: 0.8rem; opacity: 0.85; margin-top: 6px; display: inline-block;">
                                ¡Sé el primero en compartir tu opinión o teoría sobre los acontecimientos!
                            </span>
                        </div>
                    `;
                    return;
                }

                const comments = [];
                snapshot.forEach(doc => {
                    comments.push({ id: doc.id, ...doc.data() });
                });

                // Ordenar por fecha cronológica (los más recientes abajo)
                comments.sort((a, b) => (a.created_at || 0) - (b.created_at || 0));

                if (countBadge) countBadge.textContent = String(comments.length);

                container.innerHTML = comments.map(c => {
                    const author = escapeCommentHtml(c.author_name || 'Lector anónimo');
                    const initial = author.charAt(0).toUpperCase() || 'L';
                    const text = escapeCommentHtml(c.content || '');
                    const dateStr = formatCommentTimestamp(c.created_at);
                    const editionBadge = c.edition ? `<span class="comment-edition-badge">${escapeCommentHtml(c.edition)}</span>` : '';

                    return `
                        <div class="comment-item">
                            <div class="comment-avatar">${initial}</div>
                            <div class="comment-content-wrap">
                                <div class="comment-meta">
                                    <span class="comment-author-name">${author}</span>
                                    ${editionBadge}
                                    <span class="comment-date">• ${dateStr}</span>
                                </div>
                                <div class="comment-body-text">${text}</div>
                            </div>
                        </div>
                    `;
                }).join('');
            })
            .catch(err => {
                console.warn('Error leyendo comentarios de Firestore:', err);
                // Si la colección aún no existe o está inicializándose en Firestore
                if (countBadge) countBadge.textContent = '0';
                container.innerHTML = `
                    <div class="comments-empty-state">
                        💬 Comparte tu opinión o teoría sobre este capítulo.
                    </div>
                `;
            });
    }

    function publishChapterComment() {
        const authorInput = document.getElementById('comment-author-input');
        const textInput = document.getElementById('comment-text-input');
        const submitBtn = document.getElementById('btn-submit-comment');
        const statusSpan = document.getElementById('comment-form-status');

        if (!textInput || !textInput.value.trim()) return;

        const authorName = (authorInput && authorInput.value.trim()) ? authorInput.value.trim() : 'Lector anónimo';
        const contentText = textInput.value.trim();
        const currentChap = NOVEL_DATA.chapters[currentChapterIndex];
        if (!currentChap) return;

        // Guardar nombre para que el lector no tenga que reescribirlo
        localStorage.setItem('sombra_commenter_name', authorName);

        const db = getFirestoreDb();
        if (!db) {
            alert('El servicio de comentarios se está conectando. Por favor, reintenta en un momento.');
            return;
        }

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>Publicando...</span> ⏳';
        }
        if (statusSpan) {
            statusSpan.textContent = 'Guardando tu comentario...';
            statusSpan.style.color = '#38bdf8';
        }

        const newComment = {
            chapter_id: currentChap.id,
            author_name: authorName,
            content: contentText,
            edition: currentEdition || 'general',
            created_at: Date.now()
        };

        db.collection('comments').add(newComment)
            .then(() => {
                textInput.value = '';
                if (statusSpan) {
                    statusSpan.textContent = '✓ ¡Comentario publicado con éxito!';
                    statusSpan.style.color = '#34d399';
                    setTimeout(() => {
                        statusSpan.textContent = 'Tu comentario es visible de inmediato para todos los lectores.';
                        statusSpan.style.color = '';
                    }, 4000);
                }
                fetchChapterComments(currentChap.id);
            })
            .catch(err => {
                console.error('Error publicando comentario:', err);
                if (statusSpan) {
                    statusSpan.textContent = 'Error al publicar. Verifica tu conexión e inténtalo de nuevo.';
                    statusSpan.style.color = '#f87171';
                }
            })
            .finally(() => {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span>Publicar Comentario</span> 🚀';
                }
            });
    }

    function updateNavButtons() {
        if (currentChapterIndex > 0) {
            btnPrevChapter.style.display = 'flex';
            prevChapterTitle.textContent = NOVEL_DATA.chapters[currentChapterIndex - 1].title;
        } else {
            btnPrevChapter.style.display = 'none';
        }

        if (currentChapterIndex < NOVEL_DATA.chapters.length - 1) {
            btnNextChapter.style.display = 'flex';
            nextChapterTitle.textContent = NOVEL_DATA.chapters[currentChapterIndex + 1].title;
        } else {
            btnNextChapter.style.display = 'none';
        }
    }

    // --- LIMPIEZA DE CARACTERES Y SINTAXIS LATEX ---
    function cleanLatexTokens(str) {
        if (!str) return '';
        return str
            .replace(/\\dots/g, '…')
            .replace(/\\mathbf\{([^}]+)\}/g, '<strong>$1</strong>')
            .replace(/\\textbf\{([^}]+)\}/g, '<strong>$1</strong>')
            .replace(/\\textit\{([^}]+)\}/g, '<em>$1</em>')
            .replace(/\\text\{([^}]+)\}/g, '$1')
            .replace(/\\to/g, '→')
            .replace(/\\approx/g, '≈')
            .replace(/\\sim/g, '~')
            .replace(/\\times/g, '×')
            .replace(/\^\\circ\s*C?/g, '°C')
            .replace(/\^\\circ/g, '°')
            .replace(/\\vec\{([^}]+)\}/g, '$1')
            .replace(/NO_x/g, 'NO<sub>x</sub>')
            .replace(/O_3/g, 'O<sub>3</sub>')
            .replace(/O_2/g, 'O<sub>2</sub>')
            .replace(/N_2/g, 'N<sub>2</sub>')
            .replace(/CO_2/g, 'CO<sub>2</sub>')
            .replace(/\$([^\$]+)\$/g, '$1');
    }

    // --- PARSER DE MARKDOWN PARA CAPÍTULOS ---
    function parseChapterBody(rawMarkdown) {
        let text = rawMarkdown.replace(/^#\s+Capítulo\s+\d+:.*$/m, '');
        text = text.replace(/### FICHA DE LA ESCENA[\s\S]*?---/g, '');
        text = cleanLatexTokens(text);

        // Convertir divisores `---` en divisores elegantes
        text = text.replace(/^---$/gm, '<div class="scene-divider"><span class="scene-divider-icon">✦</span></div>');

        // Imágenes e Ilustraciones de Escena 16:9
        text = text.replace(/!\[(.*?)\]\((.*?)\)\s*\n\*Figura (.*?)\*/g, (match, alt, src, fig) => {
            return `<figure class="scene-illustration-figure">
                <div class="scene-illustration-frame">
                    <img src="${src}" alt="${alt}" class="scene-illustration-img" onerror="if(!this.dataset.retry){this.dataset.retry=1;this.src=this.src.replace(/\\.(png|jpg)$/, &quot;.svg&quot;);}">
                </div>
                <figcaption class="scene-illustration-caption"><strong>Figura ${fig}</strong></figcaption>
            </figure>`;
        });
        text = text.replace(/!\[(.*?)\]\((.*?)\)/g, (match, alt, src) => {
            return `<figure class="scene-illustration-figure"><img src="${src}" alt="${alt}" class="scene-illustration-img" onerror="if(!this.dataset.retry){this.dataset.retry=1;this.src=this.src.replace(/\\.(png|jpg)$/, &quot;.svg&quot;);}"></figure>`;
        });

        // Encabezados
        text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>');

        // Código y Consolas
        text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Formato
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Párrafos y Listas con soporte para saltos de línea
        const lines = text.split(/\n\s*\n/);
        const parsedParagraphs = lines.map(block => {
            let trimmed = block.trim();
            if (!trimmed) return '';
            if (trimmed.startsWith('<h') || trimmed.startsWith('<div') || trimmed.startsWith('<pre') || trimmed.startsWith('<figure')) {
                return trimmed;
            }
            // Soporte para saltos de línea de Markdown (dos o más espacios al final de línea o saltos explícitos)
            trimmed = trimmed.replace(/[ \t]{2,}\n/g, '<br>');
            // Soporte para viñetas y listas compactas dentro de un mismo bloque
            trimmed = trimmed.replace(/\n(?=\s*[•\-])/g, '<br>');
            trimmed = trimmed.replace(/\n(?=\s*\d+\.\s)/g, '<br>');

            const isBullet = trimmed.startsWith('•') || trimmed.startsWith('-') || /^\d+\.\s/.test(trimmed) || trimmed.includes('<br>•');
            const cls = isBullet ? ' class="novel-bullet-list"' : '';
            return `<p${cls}>${trimmed}</p>`;
        });

        return parsedParagraphs.join('\n');
    }

    function renderMarkdown(md) {
        if (!md) return '';
        try {
            let text = md;
            text = cleanLatexTokens(text);
            
            // Ocultar bloques mermaid no compatibles en HTML estático
            text = text.replace(/```mermaid[\s\S]*?```/g, '');
            text = text.replace(/```[\s\S]*?```/g, '');

            // Imágenes
            text = text.replace(/!\[(.*?)\]\((.*?)\)/g, '<img src="$2" alt="$1">');

            // Encabezados
            text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
            text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>');
            text = text.replace(/^# (.*$)/gim, '<h1>$1</h1>');

            // Citas / Blockquotes
            text = text.replace(/^>\s*(.*$)/gim, '<blockquote>$1</blockquote>');

            // Formato de texto
            text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

            // Listas
            text = text.replace(/^\* (.*$)/gim, '<li>$1</li>');
            text = text.replace(/^\d+\.\s+(.*$)/gim, '<li>$1</li>');

            // Tablas (convertir filas con |)
            text = text.replace(/^\|(.*)\|$/gim, (match, content) => {
                if (content.includes('---')) return '';
                const cells = content.split('|').map(c => `<td>${c.trim()}</td>`).join('');
                return `<tr>${cells}</tr>`;
            });

            // Agrupar filas de tabla en <table>
            text = text.replace(/(<tr>.*?<\/tr>\s*)+/g, match => `<table class="markdown-table">${match}</table>`);

            // Párrafos y Saltos de línea
            const blocks = text.split(/\n\s*\n/);
            const htmlBlocks = blocks.map(b => {
                const trimmed = b.trim();
                if (!trimmed) return '';
                if (trimmed.startsWith('<h') || trimmed.startsWith('<blockquote') || trimmed.startsWith('<table') || trimmed.startsWith('<li') || trimmed.startsWith('<img')) {
                    return trimmed.replace(/\n/g, '<br>');
                }
                return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`;
            });

            return htmlBlocks.join('\n');
        } catch (e) {
            console.error('Error rendering markdown:', e);
            return md;
        }
    }

    // --- RENDERIZAR SIDEBAR Y CODICES ---
    function renderSidebarList() {
        sidebarChaptersList.innerHTML = '';
        const filterText = sidebarFilter.value.toLowerCase().trim();

        NOVEL_DATA.chapters.forEach((chap, idx) => {
            if (filterText && !chap.title.toLowerCase().includes(filterText) && !chap.location.toLowerCase().includes(filterText)) {
                return;
            }

            const item = document.createElement('div');
            item.className = `chapter-item ${idx === currentChapterIndex ? 'active' : ''}`;
            item.onclick = () => loadChapter(idx);

            const isRead = readStatus[chap.id];

            item.innerHTML = `
                <div class="item-act">${chap.act.split(':')[0]} ${isRead ? '✓' : ''}</div>
                <div class="item-title">Capítulo ${chap.id}: ${chap.title}</div>
                <div class="item-meta">
                    <span>⏱️ ${chap.readTime}</span>
                    <span>📄 ~${chap.pages} págs</span>
                    <span>📍 ${chap.location.split(',')[0]}</span>
                </div>
            `;
            sidebarChaptersList.appendChild(item);
        });
    }

    function renderCodexAndEscaleta() {
        if (codexContentRendered) codexContentRendered.innerHTML = renderMarkdown(NOVEL_DATA.personajesRaw);
        if (escaletaContentRendered) escaletaContentRendered.innerHTML = renderMarkdown(NOVEL_DATA.escaletaRaw);
        if (genesisContentRendered && NOVEL_DATA.genesisRaw) {
            genesisContentRendered.innerHTML = renderMarkdown(NOVEL_DATA.genesisRaw);
        }
        const prologueContentRendered = document.getElementById('prologue-content-rendered');
        if (prologueContentRendered && NOVEL_DATA.prologoRaw) {
            prologueContentRendered.innerHTML = renderMarkdown(NOVEL_DATA.prologoRaw);
        }
    }

    // --- MARCADOR Y PROGRESO ---
    function saveBookmark() {
        bookmark = {
            chapterIndex: currentChapterIndex,
            scrollTop: window.scrollY,
            title: NOVEL_DATA.chapters[currentChapterIndex].title
        };
        localStorage.setItem('prometheus_bookmark', JSON.stringify(bookmark));
        updateBookmarkState();

        bookmarkText.textContent = '¡Guardado!';
        setTimeout(updateBookmarkState, 1500);
    }

    function updateBookmarkState() {
        if (bookmark && bookmark.chapterIndex === currentChapterIndex) {
            bookmarkText.textContent = 'Marcador Guardado';
            btnBookmark.style.borderColor = 'var(--accent-amber)';
        } else {
            bookmarkText.textContent = 'Guardar Marcador';
            btnBookmark.style.borderColor = 'var(--border-color)';
        }
    }

    function updateProgressBar() {
        if (isProgressBarUpdating) return;
        if (coverLandingView && coverLandingView.style.display !== 'none') {
            if (progressBar) progressBar.style.width = '0%';
            return;
        }
        isProgressBarUpdating = true;

        window.requestAnimationFrame(() => {
            const scrollTop = window.scrollY || document.documentElement.scrollTop || 0;
            const docHeight = (document.documentElement.scrollHeight || document.body.scrollHeight) - window.innerHeight;
            
            // Cálculo del progreso global acumulativo de toda la novela
            let totalNovelProgress = 0;
            if (typeof NOVEL_DATA !== 'undefined' && NOVEL_DATA.chapters && NOVEL_DATA.chapters.length > 0) {
                let totalWords = 0;
                let wordsBeforeCurrent = 0;

                for (let i = 0; i < NOVEL_DATA.chapters.length; i++) {
                    const cWords = NOVEL_DATA.chapters[i].words || (NOVEL_DATA.chapters[i].content ? NOVEL_DATA.chapters[i].content.length : 1000);
                    totalWords += cWords;
                    if (i < currentChapterIndex) {
                        wordsBeforeCurrent += cWords;
                    }
                }

                const currentChapterWords = NOVEL_DATA.chapters[currentChapterIndex]
                    ? (NOVEL_DATA.chapters[currentChapterIndex].words || (NOVEL_DATA.chapters[currentChapterIndex].content ? NOVEL_DATA.chapters[currentChapterIndex].content.length : 1000))
                    : 1000;

                const currentScrollFraction = docHeight > 0 ? Math.min(1, Math.max(0, scrollTop / docHeight)) : 0;
                const readWordsInCurrent = currentChapterWords * currentScrollFraction;

                const grandTotalRead = wordsBeforeCurrent + readWordsInCurrent;
                totalNovelProgress = totalWords > 0 ? Math.min(100, Math.max(0, (grandTotalRead / totalWords) * 100)) : 0;
            } else {
                totalNovelProgress = docHeight > 0 ? Math.min(100, Math.max(0, (scrollTop / docHeight) * 100)) : 0;
            }

            if (progressBar) {
                progressBar.style.width = `${totalNovelProgress.toFixed(1)}%`;
                progressBar.setAttribute('aria-valuenow', Math.round(totalNovelProgress));
                const container = document.getElementById('progress-bar-container');
                if (container) {
                    container.setAttribute('title', `Progreso total de la novela: ${Math.round(totalNovelProgress)}%`);
                }
            }

            if (headerChapterIndicator && typeof NOVEL_DATA !== 'undefined' && NOVEL_DATA.totalChapters) {
                headerChapterIndicator.textContent = `Capítulo ${currentChapterIndex + 1} de ${NOVEL_DATA.totalChapters} • ${Math.round(totalNovelProgress)}% total`;
            }

            if (btnScrollTop) {
                if (scrollTop > 400) {
                    btnScrollTop.classList.add('visible');
                } else {
                    btnScrollTop.classList.remove('visible');
                }
            }

            isProgressBarUpdating = false;
        });
    }

    // --- SIDEBAR CONTROL ---
    function openSidebar() {
        sidebar.classList.add('open');
        sidebarOverlay.classList.add('open');
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        sidebarOverlay.classList.remove('open');
    }

    // --- MODALES CONTROL ---
    window.openModal = function(id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.remove('hidden');

        if (id === 'modal-genesis') {
            const genesisContainer = document.getElementById('genesis-content');
            if (genesisContainer && typeof NOVEL_DATA !== 'undefined' && NOVEL_DATA.genesisRaw) {
                genesisContainer.innerHTML = renderMarkdown(NOVEL_DATA.genesisRaw);
            }
        }
    };

    window.closeModal = function(id) {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    };

    // --- MODO ENFOQUE ---
    function toggleFocusMode() {
        document.body.classList.toggle('focus-mode');
        if (document.body.classList.contains('focus-mode')) {
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen().catch(() => {});
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen().catch(() => {});
            }
        }
    }

    // --- BUSCADOR GLOBAL ---
    function handleGlobalSearch(e) {
        const query = e.target.value.trim().toLowerCase();
        searchResultsList.innerHTML = '';

        if (query.length < 2) {
            searchResultsList.innerHTML = '<p class="search-placeholder">Introduce al menos 2 caracteres para buscar en todos los capítulos...</p>';
            return;
        }

        let matchCount = 0;

        NOVEL_DATA.chapters.forEach((chap, idx) => {
            const contentLower = chap.content.toLowerCase();
            let pos = contentLower.indexOf(query);

            if (pos !== -1) {
                matchCount++;
                const start = Math.max(0, pos - 60);
                const end = Math.min(chap.content.length, pos + 100);
                let snippet = chap.content.substring(start, end).replace(/\n/g, ' ');
                
                const regex = new RegExp(`(${query})`, 'gi');
                snippet = snippet.replace(regex, '<span class="highlight">$1</span>');

                const item = document.createElement('div');
                item.className = 'search-result-item';
                item.onclick = () => {
                    closeModal('modal-search');
                    loadChapter(idx);
                };
                item.innerHTML = `
                    <div class="search-result-title">Capítulo ${chap.id}: ${chap.title}</div>
                    <div class="search-result-snippet">"...${snippet}..."</div>
                `;
                searchResultsList.appendChild(item);
            }
        });

        if (matchCount === 0) {
            searchResultsList.innerHTML = '<p class="search-placeholder">No se encontraron coincidencias para tu búsqueda.</p>';
        }
    }

    // --- SINTETIZADOR DE AMBIENTE SONORO (WEB AUDIO API) ---
    function toggleAmbientSound() {
        if (!audioContext) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            audioContext = new AudioContext();
        }

        if (isAudioPlaying) {
            stopAmbientSound();
        } else {
            startAmbientSound();
        }
    }

    function startAmbientSound() {
        if (!audioContext) return;
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }

        ambientGain = audioContext.createGain();
        ambientGain.gain.setValueAtTime(0.04, audioContext.currentTime);

        const bufferSize = audioContext.sampleRate * 2;
        const noiseBuffer = audioContext.createBuffer(1, bufferSize, audioContext.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            output[i] = Math.random() * 2 - 1;
        }

        const whiteNoise = audioContext.createBufferSource();
        whiteNoise.buffer = noiseBuffer;
        whiteNoise.loop = true;

        const filter = audioContext.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(160, audioContext.currentTime);

        whiteNoise.connect(filter);
        filter.connect(ambientGain);
        ambientGain.connect(audioContext.destination);

        whiteNoise.start();
        isAudioPlaying = true;

        btnToggleAudio.classList.add('active');
        btnToggleAudio.style.borderColor = 'var(--accent-pink)';
        btnToggleAudio.style.color = 'var(--accent-pink)';
    }

    function stopAmbientSound() {
        if (ambientGain) {
            ambientGain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.5);
            setTimeout(() => {
                isAudioPlaying = false;
                btnToggleAudio.classList.remove('active');
                btnToggleAudio.style.borderColor = 'var(--border-color)';
                btnToggleAudio.style.color = 'var(--text-primary)';
            }, 500);
        }
    }

    // --- ATAJOS DE TECLADO ---
    function handleKeyboardShortcuts(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if (e.key === 'ArrowLeft') {
            if (currentChapterIndex > 0) loadChapter(currentChapterIndex - 1);
        } else if (e.key === 'ArrowRight') {
            if (currentChapterIndex < NOVEL_DATA.chapters.length - 1) loadChapter(currentChapterIndex + 1);
        } else if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(m => m.classList.add('hidden'));
            closeSidebar();
        } else if (e.key === 'f' || e.key === 'F') {
            toggleFocusMode();
        }
    }

    /* ==========================================================================
       LÓGICA Y MOTOR DEL REPRODUCTOR DE AUDIOLIBRO (TTS Y SINTETIZADOR)
       ========================================================================== */

    function initAudiobook() {
        if (!abTrackSelect) return;

        // Parsear biografías
        abParsedBios = parseBiografiasData();

        // Poblar Selector de Capítulos
        abOptgroupChapters.innerHTML = '';
        NOVEL_DATA.chapters.forEach((chap, idx) => {
            const opt = document.createElement('option');
            opt.value = `chapter-${idx}`;
            opt.textContent = `Capítulo ${chap.id}: ${chap.title}`;
            abOptgroupChapters.appendChild(opt);
        });

        // Poblar Selector de Biografías
        abOptgroupBios.innerHTML = '';
        abParsedBios.forEach((bio, idx) => {
            const opt = document.createElement('option');
            opt.value = `bio-${idx}`;
            opt.textContent = `Biografía: ${bio.name}`;
            abOptgroupBios.appendChild(opt);
        });

        // Cargar voces del sistema TTS
        loadTTSVoices();
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadTTSVoices;
        }

        // Registrar Eventos del Reproductor
        abTrackSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            const [type, idxStr] = val.split('-');
            const idx = parseInt(idxStr, 10);
            loadAudiobookTrack(type, idx);
            if (abIsPlaying) playAudiobook();
        });

        abBtnPlay.addEventListener('click', togglePlayPauseAudiobook);

        abBtnPrev.addEventListener('click', () => {
            if (abCurrentTrackIndex > 0) {
                loadAudiobookTrack(abCurrentTrackType, abCurrentTrackIndex - 1);
                if (abIsPlaying) playAudiobook();
            }
        });

        abBtnNext.addEventListener('click', () => {
            const maxIdx = abCurrentTrackType === 'chapter' ? NOVEL_DATA.chapters.length - 1 : abParsedBios.length - 1;
            if (abCurrentTrackIndex < maxIdx) {
                loadAudiobookTrack(abCurrentTrackType, abCurrentTrackIndex + 1);
                if (abIsPlaying) playAudiobook();
            }
        });

        abBtnRewind.addEventListener('click', () => skipAudiobookParagraph(-1));
        abBtnForward.addEventListener('click', () => skipAudiobookParagraph(1));

        abSpeedSelect.addEventListener('change', () => {
            if (abIsPlaying) playAudiobookParagraph(abActiveParagraphIndex);
        });

        if (abVocalProfile) {
            abVocalProfile.addEventListener('change', () => {
                if (abIsPlaying) playAudiobookParagraph(abActiveParagraphIndex);
            });
        }

        abAmbientVol.addEventListener('input', (e) => {
            const vol = parseFloat(e.target.value);
            if (vol > 0 && !isAudioPlaying) {
                startAmbientSound();
            }
            if (ambientGain && audioContext) {
                ambientGain.gain.setValueAtTime(vol * 0.15, audioContext.currentTime);
            }
        });
    }

    function parseBiografiasData() {
        if (!NOVEL_DATA.biografiasRaw) return [];
        const bios = [];
        const raw = NOVEL_DATA.biografiasRaw;
        const sections = raw.split(/###\s+\d+\.\s+/);

        sections.slice(1).forEach((sec, idx) => {
            const lines = sec.split('\n');
            const nameHeader = lines[0].trim();
            const cleanName = nameHeader.replace(/\(.*\)/, '').trim();

            let coverImg = 'cover.png';
            const imgMatch = sec.match(/\[`img\/(.*?)`\]/);
            if (imgMatch && imgMatch[1]) {
                coverImg = 'img/' + imgMatch[1];
            } else if (idx === 0) coverImg = 'img/char_cole_vance.png';
            else if (idx === 1) coverImg = 'img/char_maya_lin.png';
            else if (idx === 2) coverImg = 'img/char_kael_glitch.png';
            else if (idx === 3) coverImg = 'img/char_bob_robot.png';
            else if (idx === 4) coverImg = 'img/char_padre_thomas.png';
            else if (idx === 5) coverImg = 'img/char_aura_prototype.png';
            else if (idx === 6) coverImg = 'img/char_sterling_hayes.png';
            else if (idx === 7) coverImg = 'img/char_marcus_bennett.png';

            // Limpiar texto para párrafos
            const bodyLines = lines.slice(1).filter(l => !l.startsWith('---'));
            const fullText = bodyLines.join('\n');
            const rawParagraphs = fullText.split(/\n\n+/);
            const paragraphs = rawParagraphs
                .map(p => p.replace(/[\*#_`]/g, '').replace(/\[.*?\]\(.*?\)/g, '').trim())
                .filter(p => p.length > 5);

            bios.push({
                id: idx,
                name: cleanName,
                fullName: nameHeader,
                coverImage: coverImg,
                paragraphs: paragraphs
            });
        });
        return bios;
    }

    function loadTTSVoices() {
        if (!abSpeechSynth) return;
        abVoices = abSpeechSynth.getVoices();
        if (!abVoices || abVoices.length === 0) return;

        abVoiceSelect.innerHTML = '';
        
        // Priorizar voces en español
        const esVoices = abVoices.filter(v => v.lang.startsWith('es'));
        const displayVoices = esVoices.length > 0 ? esVoices : abVoices;

        displayVoices.forEach((voice, index) => {
            const option = document.createElement('option');
            option.value = voice.name;
            option.textContent = `${voice.name} (${voice.lang})`;
            if (voice.default || (index === 0 && esVoices.length > 0)) {
                option.selected = true;
            }
            abVoiceSelect.appendChild(option);
        });
    }

    function openAudiobookModal(type = 'chapter', index = 0) {
        loadAudiobookTrack(type, index);
        openModal('modal-audiobook');
    }

    function loadAudiobookTrack(type, index) {
        stopAudiobookSpeech();

        abCurrentTrackType = type;
        abCurrentTrackIndex = index;
        abTrackSelect.value = `${type}-${index}`;

        if (type === 'chapter') {
            const chap = NOVEL_DATA.chapters[index];
            abTrackTitle.textContent = `Capítulo ${chap.id}: ${chap.title}`;
            abTrackMeta.textContent = `${chap.act} • POV: ${chap.pov} • ${chap.location}`;
            abCoverImg.src = chap.povImage || 'cover.png';

            // Extraer párrafos limpios del contenido del capítulo
            const cleanText = chap.content.replace(/^#+.*$/gm, '').replace(/!\[.*?\]\(.*?\)/g, '');
            abParagraphs = cleanText.split(/\n\n+/).map(p => p.replace(/[\*#_`]/g, '').trim()).filter(p => p.length > 5);
        } else {
            const bio = abParsedBios[index];
            abTrackTitle.textContent = `Biografía: ${bio.fullName}`;
            abTrackMeta.textContent = `Perfil de Personaje • Lore Oficial`;
            abCoverImg.src = bio.coverImage;
            abParagraphs = bio.paragraphs;
        }

        abActiveParagraphIndex = 0;
        renderAudiobookTranscript();
        updateAudiobookProgressUI();
    }

    function renderAudiobookTranscript() {
        abTranscriptBody.innerHTML = '';
        abParagraphs.forEach((pText, pIdx) => {
            const pEl = document.createElement('div');
            pEl.className = 'transcript-paragraph';
            if (pIdx === abActiveParagraphIndex) pEl.classList.add('active-speaking-paragraph');
            pEl.textContent = pText;

            pEl.addEventListener('click', () => {
                abActiveParagraphIndex = pIdx;
                playAudiobookParagraph(pIdx);
            });

            abTranscriptBody.appendChild(pEl);
        });
    }

    function togglePlayPauseAudiobook() {
        if (abIsPlaying) {
            pauseAudiobook();
        } else {
            playAudiobook();
        }
    }

    function playAudiobook() {
        abIsPlaying = true;
        abPlayIcon.textContent = '⏸';
        abEqualizer.classList.remove('hidden');

        // Activar el Sintetizador Sonoro de Fondo según el perfil seleccionado
        const profile = abVocalProfile ? abVocalProfile.value : 'dramatic';
        const preset = abSoundscapePreset ? abSoundscapePreset.value : 'auto';
        const activeSound = preset !== 'auto' ? preset : profile;
        applyWebAudioSoundscape(activeSound);

        playAudiobookParagraph(abActiveParagraphIndex);
    }

    function pauseAudiobook() {
        abIsPlaying = false;
        abPlayIcon.textContent = '▶';
        abEqualizer.classList.add('hidden');
        stopAudiobookSpeech();
        stopWebAudioSoundscape();
        abStatusText.textContent = 'Pausado';
    }

    function stopAudiobookSpeech() {
        if (abSpeechSynth) abSpeechSynth.cancel();
    }

    function playAudiobookParagraph(pIdx) {
        if (pIdx < 0 || pIdx >= abParagraphs.length) {
            pauseAudiobook();
            abStatusText.textContent = 'Fin del track';
            return;
        }

        stopAudiobookSpeech();

        abActiveParagraphIndex = pIdx;
        updateAudiobookProgressUI();

        // Destacar el párrafo en la transcripción
        const pEls = abTranscriptBody.querySelectorAll('.transcript-paragraph');
        pEls.forEach((el, i) => {
            if (i === pIdx) {
                el.classList.add('active-speaking-paragraph');
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                el.classList.remove('active-speaking-paragraph');
            }
        });

        const textToSpeak = abParagraphs[pIdx];
        const utterance = new SpeechSynthesisUtterance(textToSpeak);

        // Seleccionar Voz TTS
        const selectedVoiceName = abVoiceSelect ? abVoiceSelect.value : '';
        if (selectedVoiceName && abVoices.length > 0) {
            const vObj = abVoices.find(v => v.name === selectedVoiceName);
            if (vObj) utterance.voice = vObj;
        }

        // Aplicar Perfil Vocal y Prosodia Dramática (Pitch & Rate modulation)
        const profile = abVocalProfile ? abVocalProfile.value : 'dramatic';
        let baseRate = parseFloat(abSpeedSelect.value) || 0.9;
        let basePitch = 1.0;

        if (profile === 'dramatic') {
            basePitch = 0.85; // Voz más grave y teatral de thriller
            baseRate = baseRate * 0.95;
        } else if (profile === 'cole') {
            basePitch = 1.05; // POV Cole Vance (joven, analítico)
            baseRate = baseRate * 1.0;
        } else if (profile === 'maya') {
            basePitch = 1.15; // POV Maya Lin (periodista, decidida)
            baseRate = baseRate * 1.05;
        } else if (profile === 'bob') {
            basePitch = 0.72; // BOB el Robot (sintético profundo)
            baseRate = baseRate * 0.88;
        } else if (profile === 'thomas') {
            basePitch = 0.80; // Padre Thomas (solemne, grave)
            baseRate = baseRate * 0.85;
        } else if (profile === 'aura') {
            basePitch = 1.20; // AURA / ASI (cristalina superinteligencia)
            baseRate = baseRate * 0.95;
        }

        utterance.pitch = Math.max(0.5, Math.min(1.5, basePitch));
        utterance.rate = Math.max(0.5, Math.min(2.0, baseRate));

        utterance.onend = () => {
            if (abIsPlaying) {
                if (abActiveParagraphIndex < abParagraphs.length - 1) {
                    playAudiobookParagraph(abActiveParagraphIndex + 1);
                } else {
                    pauseAudiobook();
                    abStatusText.textContent = 'Pista completada';
                }
            }
        };

        utterance.onerror = (e) => {
            console.warn('TTS Speech Error:', e);
            pauseAudiobook();
        };

        abCurrentUtterance = utterance;
        abSpeechSynth.speak(utterance);
        abStatusText.textContent = `Narrando [${profile.toUpperCase()}] (${utterance.rate.toFixed(2)}x)...`;
    }

    function skipAudiobookParagraph(delta) {
        const nextIdx = abActiveParagraphIndex + delta;
        if (nextIdx >= 0 && nextIdx < abParagraphs.length) {
            playAudiobookParagraph(nextIdx);
        }
    }

    function updateAudiobookProgressUI() {
        const total = abParagraphs.length;
        const current = abActiveParagraphIndex + 1;
        abCurrentTime.textContent = `Párrafo ${current} / ${total}`;
        const pct = total > 0 ? (current / total) * 100 : 0;
        abProgressBar.style.width = `${pct}%`;
    }

    /* --- SINTETIZADOR WEB AUDIO API PARA SOUNDSCAPES Y AMBIENTE --- */
    let soundscapeCtx = null;
    let soundscapeNodes = [];

    function applyWebAudioSoundscape(profileName) {
        stopWebAudioSoundscape();

        if (!soundscapeCtx) {
            soundscapeCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (soundscapeCtx.state === 'suspended') {
            soundscapeCtx.resume();
        }

        const masterGain = soundscapeCtx.createGain();
        const volVal = abAmbientVol ? parseFloat(abAmbientVol.value) : 0.25;
        masterGain.gain.setValueAtTime(volVal * 0.18, soundscapeCtx.currentTime);
        masterGain.connect(soundscapeCtx.destination);

        if (profileName === 'dramatic') {
            // Drone sub-bass cinematográfico (55Hz sine + 110Hz triangle)
            const osc1 = soundscapeCtx.createOscillator();
            const osc2 = soundscapeCtx.createOscillator();
            const filter = soundscapeCtx.createBiquadFilter();

            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(55, soundscapeCtx.currentTime);
            osc2.type = 'triangle';
            osc2.frequency.setValueAtTime(110, soundscapeCtx.currentTime);

            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(140, soundscapeCtx.currentTime);

            osc1.connect(filter);
            osc2.connect(filter);
            filter.connect(masterGain);

            osc1.start();
            osc2.start();
            soundscapeNodes.push(osc1, osc2, filter, masterGain);

        } else if (profileName === 'bob') {
            // Zumbido cibernético robótico (110Hz sawtooth + LFO de modulación de frecuencia)
            const osc = soundscapeCtx.createOscillator();
            const lfo = soundscapeCtx.createOscillator();
            const filter = soundscapeCtx.createBiquadFilter();
            const lfoGain = soundscapeCtx.createGain();

            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(110, soundscapeCtx.currentTime);

            filter.type = 'bandpass';
            filter.frequency.setValueAtTime(600, soundscapeCtx.currentTime);
            filter.Q.setValueAtTime(5, soundscapeCtx.currentTime);

            lfo.type = 'sine';
            lfo.frequency.setValueAtTime(4, soundscapeCtx.currentTime);
            lfoGain.gain.setValueAtTime(200, soundscapeCtx.currentTime);

            lfo.connect(lfoGain);
            lfoGain.connect(filter.frequency);
            osc.connect(filter);
            filter.connect(masterGain);

            osc.start();
            lfo.start();
            soundscapeNodes.push(osc, lfo, filter, lfoGain, masterGain);

        } else if (profileName === 'aura') {
            // Acorde flotante harmónico de superinteligencia (220Hz + 440Hz + 660Hz)
            const osc1 = soundscapeCtx.createOscillator();
            const osc2 = soundscapeCtx.createOscillator();
            const osc3 = soundscapeCtx.createOscillator();
            const filter = soundscapeCtx.createBiquadFilter();

            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(220, soundscapeCtx.currentTime);
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(440, soundscapeCtx.currentTime);
            osc3.type = 'sine';
            osc3.frequency.setValueAtTime(660, soundscapeCtx.currentTime);

            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(800, soundscapeCtx.currentTime);

            osc1.connect(filter);
            osc2.connect(filter);
            osc3.connect(filter);
            filter.connect(masterGain);

            osc1.start();
            osc2.start();
            osc3.start();
            soundscapeNodes.push(osc1, osc2, osc3, filter, masterGain);

        } else if (profileName === 'thomas' || profileName === 'catacombs') {
            // Tono de órgano / catedral místico (130.81Hz + 196Hz)
            const osc1 = soundscapeCtx.createOscillator();
            const osc2 = soundscapeCtx.createOscillator();
            const filter = soundscapeCtx.createBiquadFilter();

            osc1.type = 'triangle';
            osc1.frequency.setValueAtTime(130.81, soundscapeCtx.currentTime);
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(196, soundscapeCtx.currentTime);

            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(320, soundscapeCtx.currentTime);

            osc1.connect(filter);
            osc2.connect(filter);
            filter.connect(masterGain);

            osc1.start();
            osc2.start();
            soundscapeNodes.push(osc1, osc2, filter, masterGain);

        } else if (profileName === 'maya' || profileName === 'rain') {
            // Lluvia urbana y ruido suavizado
            const bufferSize = soundscapeCtx.sampleRate * 2;
            const noiseBuffer = soundscapeCtx.createBuffer(1, bufferSize, soundscapeCtx.sampleRate);
            const output = noiseBuffer.getChannelData(0);
            let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0;
            for (let i = 0; i < bufferSize; i++) {
                let white = Math.random() * 2 - 1;
                b0 = 0.99886 * b0 + white * 0.0555179;
                b1 = 0.99332 * b1 + white * 0.0750759;
                b2 = 0.96900 * b2 + white * 0.1538520;
                b3 = 0.86650 * b3 + white * 0.3104856;
                b4 = 0.55000 * b4 + white * 0.5329522;
                b5 = -0.7616 * b5 - white * 0.0168980;
                output[i] = (b0 + b1 + b2 + b3 + b4 + b5 + white * 0.5362) * 0.08;
            }

            const whiteNoise = soundscapeCtx.createBufferSource();
            whiteNoise.buffer = noiseBuffer;
            whiteNoise.loop = true;

            const filter = soundscapeCtx.createBiquadFilter();
            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(380, soundscapeCtx.currentTime);

            whiteNoise.connect(filter);
            filter.connect(masterGain);
            whiteNoise.start();
            soundscapeNodes.push(whiteNoise, filter, masterGain);
        }
    }

    function stopWebAudioSoundscape() {
        soundscapeNodes.forEach(node => {
            try {
                if (node.stop) node.stop();
                if (node.disconnect) node.disconnect();
            } catch (e) {}
        });
        soundscapeNodes = [];
    }
});

