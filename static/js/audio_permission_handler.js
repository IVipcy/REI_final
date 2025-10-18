// 音声再生許可ハンドラー
(function() {
    'use strict';
    
    let audioPermissionGranted = false;
    let pendingAudioElements = [];
    
    // 音声再生許可を取得する関数
    window.requestAudioPermission = function() {
        if (audioPermissionGranted) return Promise.resolve();
        
        return new Promise((resolve) => {
            // ダミーの音声を作成して再生試行
            const dummyAudio = new Audio();
            dummyAudio.src = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQgAAAAAAAAAAAAA';
            dummyAudio.volume = 0.01;
            
            const playPromise = dummyAudio.play();
            
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        audioPermissionGranted = true;
                        console.log('✅ 音声再生許可を取得しました');
                        
                        // 保留中の音声を再生
                        pendingAudioElements.forEach(audio => {
                            audio.play().catch(e => console.warn('保留音声の再生失敗:', e));
                        });
                        pendingAudioElements = [];
                        
                        resolve();
                    })
                    .catch(() => {
                        console.log('⚠️ 音声再生許可が必要です');
                        resolve();
                    });
            }
        });
    };
    
    // ページ読み込み時に自動的に許可を試行
    document.addEventListener('DOMContentLoaded', function() {
        // 最初のユーザーインタラクションで音声許可を取得
        const enableAudio = function() {
            requestAudioPermission();
            document.removeEventListener('click', enableAudio);
            document.removeEventListener('touchstart', enableAudio);
            document.removeEventListener('keydown', enableAudio);
        };
        
        document.addEventListener('click', enableAudio);
        document.addEventListener('touchstart', enableAudio);
        document.addEventListener('keydown', enableAudio);
        
        // 言語選択ボタンのクリックでも音声許可を取得
        const languageButtons = document.querySelectorAll('#select-japanese, #select-english');
        languageButtons.forEach(button => {
            button.addEventListener('click', requestAudioPermission);
        });
    });
    
    // 音声再生をラップする関数
    window.playAudioWithPermission = function(audioElement) {
        if (audioPermissionGranted) {
            return audioElement.play();
        } else {
            // 許可がない場合は保留リストに追加
            pendingAudioElements.push(audioElement);
            
            // 許可プロンプトを表示
            if (!document.getElementById('audio-permission-banner')) {
                const banner = document.createElement('div');
                banner.id = 'audio-permission-banner';
                banner.style.cssText = `
                    position: fixed;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #4CAF50;
                    color: white;
                    padding: 15px 30px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    z-index: 10000;
                    cursor: pointer;
                    font-size: 16px;
                    font-family: 'Noto Sans JP', sans-serif;
                    animation: slideDown 0.3s ease-out;
                `;
                banner.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span>🔊</span>
                        <span>クリックして音声を有効にする</span>
                    </div>
                `;
                
                banner.addEventListener('click', function() {
                    requestAudioPermission().then(() => {
                        banner.remove();
                    });
                });
                
                document.body.appendChild(banner);
            }
            
            return Promise.reject(new Error('Audio permission required'));
        }
    };
    
    // CSSアニメーション
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from {
                transform: translateX(-50%) translateY(-100%);
                opacity: 0;
            }
            to {
                transform: translateX(-50%) translateY(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
    
})(); 