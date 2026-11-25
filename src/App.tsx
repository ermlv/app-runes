import { useState, useCallback, useEffect } from 'react';
import { runes, Rune } from './data/runes';
import freyaImg from './assets/freya-warning.jpg';

// Тайл руны по id (порядок = id в runes.ts, файлы лежат в public/runes/)
const runeImg = (id: number) =>
  `${import.meta.env.BASE_URL}runes/rune-${String(id).padStart(2, '0')}.jpg`;

type GamePhase = 'intro' | 'drawing' | 'result';
type Position = 'past' | 'present' | 'future';

interface DrawnRune {
  rune: Rune;
  position: Position;
  isReversed: boolean;
}

function getRandomRune(exclude: number[]): { rune: Rune; isReversed: boolean } {
  const available = runes.filter(r => !exclude.includes(r.id));
  const randomIndex = Math.floor(Math.random() * available.length);
  const rune = available[randomIndex];
  // 30% шанс перевёрнутого положения (только для рун, которые могут быть перевёрнуты)
  const isReversed = rune.reversed ? Math.random() < 0.3 : false;
  return { rune, isReversed };
}

export default function App() {
  const [phase, setPhase] = useState<GamePhase>('intro');
  const [drawnRunes, setDrawnRunes] = useState<DrawnRune[]>([]);
  const [currentPosition, setCurrentPosition] = useState<Position>('past');
  const [isDrawing, setIsDrawing] = useState(false);
  const [showRune, setShowRune] = useState(false);
  const [currentDrawn, setCurrentDrawn] = useState<{ rune: Rune; isReversed: boolean } | null>(null);
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; delay: number; size: number }>>([]);
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    const newParticles = Array.from({ length: 40 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 5,
      size: Math.random() * 3 + 1,
    }));
    setParticles(newParticles);
  }, []);

  const startGame = useCallback(() => {
    setDrawnRunes([]);
    setCurrentPosition('past');
    setIsDrawing(false);
    setShowRune(false);
    setCurrentDrawn(null);
    setPhase('drawing');
  }, []);

  const drawRune = useCallback(() => {
    if (isDrawing) return;
    
    setIsDrawing(true);
    setShowRune(false);
    setCurrentDrawn(null);

    // Анимация "вытягивания" - 1.5 секунды
    setTimeout(() => {
      const exclude = drawnRunes.map(d => d.rune.id);
      const result = getRandomRune(exclude);
      setCurrentDrawn(result);
      setShowRune(true);
      
      // Через 2 секунды показываем результат и переходим к следующей
      setTimeout(() => {
        const newDrawn: DrawnRune = {
          rune: result.rune,
          position: currentPosition,
          isReversed: result.isReversed,
        };
        const newDrawnRunes = [...drawnRunes, newDrawn];
        setDrawnRunes(newDrawnRunes);
        setIsDrawing(false);

        if (currentPosition === 'past') {
          setCurrentPosition('present');
          setShowRune(false);
        } else if (currentPosition === 'present') {
          setCurrentPosition('future');
          setShowRune(false);
        } else {
          // Все три руны вытянуты
          setTimeout(() => {
            setPhase('result');
          }, 1500);
        }
      }, 2000);
    }, 1500);
  }, [isDrawing, drawnRunes, currentPosition]);

  const getPositionLabel = (pos: Position): string => {
    switch (pos) {
      case 'past': return 'Прошлое';
      case 'present': return 'Настоящее';
      case 'future': return 'Будущее';
    }
  };

  const getPositionDescription = (pos: Position): string => {
    switch (pos) {
      case 'past': return 'Причины и корни ситуации';
      case 'present': return 'Текущее состояние дел';
      case 'future': return 'К чему всё ведёт';
    }
  };

  const getRuneText = (selection: DrawnRune): string => {
    const { rune, position, isReversed } = selection;
    if (isReversed) {
      switch (position) {
        case 'past': return rune.reversedPast || rune.past;
        case 'present': return rune.reversedPresent || rune.present;
        case 'future': return rune.reversedFuture || rune.future;
      }
    }
    switch (position) {
      case 'past': return rune.past;
      case 'present': return rune.present;
      case 'future': return rune.future;
    }
  };

  // Intro Screen
  if (phase === 'intro') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-950 to-gray-900 flex items-center justify-center p-4 relative overflow-hidden">
        {/* Particles */}
        {particles.map(p => (
          <div
            key={p.id}
            className="absolute rounded-full bg-amber-200/20 animate-pulse"
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: `${p.size}px`,
              height: `${p.size}px`,
              animationDelay: `${p.delay}s`,
              animationDuration: `${2 + p.delay}s`
            }}
          />
        ))}
        
        <div className="text-center max-w-2xl relative z-10">
          {/* Mystical symbol */}
          <div className="text-8xl mb-6 animate-pulse rune-symbol">
            ᛟ
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-yellow-300 to-amber-200 mb-6 font-serif">
            Гадание на Трёх Рунах
          </h1>
          
          <p className="text-purple-200 text-lg md:text-xl mb-4 leading-relaxed">
            Древнее скандинавское гадание на рунах Старшего Футарка
          </p>
          
          <div className="bg-purple-900/30 backdrop-blur-sm border border-purple-500/30 rounded-xl p-6 mb-8 text-left">
            <h2 className="text-amber-300 text-xl font-semibold mb-4 text-center">Как работает гадание</h2>
            <div className="space-y-3 text-purple-100">
              <div className="flex items-start gap-3">
                <img src={runeImg(1)} alt="" className="inline-block w-5 h-5 rounded align-middle" />
                <p><strong className="text-amber-200">Первая руна — Прошлое:</strong> отражает события и обстоятельства, которые привели к текущей ситуации. Показывает корни и причины.</p>
              </div>
              <div className="flex items-start gap-3">
                <img src={runeImg(2)} alt="" className="inline-block w-5 h-5 rounded align-middle" />
                <p><strong className="text-amber-200">Вторая руна — Настоящее:</strong> показывает текущее состояние дел, энергию момента и силы, действующие сейчас.</p>
              </div>
              <div className="flex items-start gap-3">
                <img src={runeImg(3)} alt="" className="inline-block w-5 h-5 rounded align-middle" />
                <p><strong className="text-amber-200">Третья руна — Будущее:</strong> указывает на то, к чему ведёт текущий путь, если ничего не менять.</p>
              </div>
            </div>
            <p className="text-purple-300 text-sm mt-4 text-center italic">
              Руны выпадают случайным образом. Каждая может оказаться перевёрнутой, что меняет её толкование.
            </p>
          </div>
          
          <button
            onClick={startGame}
            className="px-8 py-4 bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white font-bold text-xl rounded-xl shadow-lg shadow-amber-600/30 transform hover:scale-105 transition-all duration-300 cursor-pointer"
          >
            ✦ Начать гадание ✦
          </button>
          
          <p className="text-purple-400 text-sm mt-6">
            Сосредоточьтесь на своём вопросе перед началом
          </p>
        </div>
      </div>
    );
  }

  // Drawing Screen
  if (phase === 'drawing') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-950 to-gray-900 flex items-center justify-center p-4 relative overflow-hidden">
        {/* Particles */}
        {particles.map(p => (
          <div
            key={p.id}
            className="absolute rounded-full bg-amber-200/15 animate-pulse"
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: `${p.size}px`,
              height: `${p.size}px`,
              animationDelay: `${p.delay}s`,
              animationDuration: `${2 + p.delay}s`
            }}
          />
        ))}

        <div className="text-center max-w-3xl relative z-10 w-full">
          <h1 className="text-3xl md:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-yellow-300 to-amber-200 font-serif mb-4">
            {drawnRunes.length === 0 ? 'Вытяните первую руну' : 
             drawnRunes.length === 1 ? 'Вытяните вторую руну' : 'Вытяните третью руну'}
          </h1>
          
          {/* Progress indicator */}
          <div className="flex justify-center gap-4 mb-8">
            {(['past', 'present', 'future'] as Position[]).map((pos, idx) => (
              <div key={pos} className="text-center">
                <div className={`w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center border-2 transition-all duration-500
                  ${idx < drawnRunes.length 
                    ? 'border-amber-400 bg-amber-900/40 shadow-lg shadow-amber-400/20' 
                    : idx === drawnRunes.length 
                      ? 'border-purple-400 bg-purple-900/40 animate-pulse' 
                      : 'border-purple-700/50 bg-purple-900/20'}`}>
                  {idx < drawnRunes.length ? (
                    <img src={runeImg(drawnRunes[idx].rune.id)} alt="" className="w-9 h-9 rounded-md object-cover" />
                  ) : (
                    <span className="text-purple-400 text-lg">{idx + 1}</span>
                  )}
                </div>
                <p className={`text-xs mt-1 ${idx <= drawnRunes.length ? 'text-amber-200' : 'text-purple-500'}`}>
                  {getPositionLabel(pos)}
                </p>
              </div>
            ))}
          </div>

          {/* Current position description */}
          <div className="bg-purple-900/40 backdrop-blur-sm border border-purple-500/30 rounded-lg px-6 py-3 inline-block mb-8">
            <p className="text-amber-300 font-semibold text-lg">
              {getPositionLabel(currentPosition)}
            </p>
            <p className="text-purple-300 text-sm">
              {getPositionDescription(currentPosition)}
            </p>
          </div>

          {/* Rune drawing area */}
          <div className="mb-8">
            {showRune && currentDrawn ? (
              <div className="animate-fade-in">
                <div className={`
                  w-32 h-40 md:w-40 md:h-48 mx-auto rounded-xl flex items-center justify-center border-3 shadow-2xl
                  ${currentDrawn.isReversed 
                    ? 'border-red-400/70 bg-gradient-to-b from-red-900/40 to-gray-900/80 shadow-red-400/30' 
                    : 'border-amber-400/70 bg-gradient-to-b from-amber-900/40 to-gray-900/80 shadow-amber-400/30'}
                  ${currentDrawn.isReversed ? 'rotate-180' : ''}
                `}>
                  <img src={runeImg(currentDrawn.rune.id)} alt="" className="w-28 h-28 md:w-36 md:h-36 rounded-xl object-cover" />
                </div>
                <p className="text-amber-200 text-xl font-bold mt-4 font-serif">
                  {currentDrawn.rune.nameRu}
                </p>
                <p className="text-purple-400 text-sm italic">
                  {currentDrawn.isReversed ? 'Перевёрнутая позиция' : 'Прямая позиция'}
                </p>
              </div>
            ) : (
              <div className={`
                w-32 h-40 md:w-40 md:h-48 mx-auto rounded-xl flex items-center justify-center border-2
                ${isDrawing 
                  ? 'border-purple-400 bg-gradient-to-b from-purple-800/60 to-gray-900/80 animate-bounce shadow-xl shadow-purple-400/30' 
                  : 'border-purple-500/50 bg-gradient-to-b from-purple-900/40 to-gray-900/60'}
              `}>
                {isDrawing ? (
                  <div className="text-center">
                    <div className="text-4xl mb-2 animate-spin">✦</div>
                    <p className="text-purple-300 text-sm">Руна выбирается...</p>
                  </div>
                ) : (
                  <div className="text-center">
                    <span className="text-5xl text-purple-400/60 rune-symbol">ᛟ</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Draw button */}
          {!showRune && (
            <button
              onClick={drawRune}
              disabled={isDrawing}
              className={`
                px-8 py-4 font-bold text-xl rounded-xl shadow-lg transform transition-all duration-300 cursor-pointer
                ${isDrawing 
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white shadow-amber-600/30 hover:scale-105'}
              `}
            >
              {isDrawing ? '✦ Руна выбирается... ✦' : '✦ Вытянуть руну ✦'}
            </button>
          )}

          <p className="text-purple-400 text-sm mt-6">
            Сосредоточьтесь на вопросе и доверьтесь судьбе
          </p>
        </div>
      </div>
    );
  }

  // Result Screen
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-950 to-gray-900 p-4 py-8 relative overflow-hidden">
      {particles.map(p => (
        <div
          key={p.id}
          className="absolute rounded-full bg-amber-200/15 animate-pulse"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            animationDelay: `${p.delay}s`,
            animationDuration: `${2 + p.delay}s`
          }}
        />
      ))}

      <div className="max-w-5xl mx-auto relative z-10">
        <h1 className="text-3xl md:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-yellow-300 to-amber-200 font-serif mb-2 text-center">
          Послание Рун
        </h1>
        <p className="text-purple-300 text-center mb-8">Три Норны раскрыли вашу судьбу</p>

        {/* Rune Cards */}
        <div className="grid md:grid-cols-[1fr_auto_1fr_auto_1fr] gap-4 items-center mb-10">
          {drawnRunes.map((sel, idx) => (
            <div key={`card-${idx}`} className="contents">
              {/* Arrow before card (except first) */}
              {idx > 0 && (
                <div className="hidden md:flex items-center justify-center text-amber-400/60 text-3xl font-bold">
                  →
                </div>
              )}
              <div
                className="bg-gradient-to-b from-purple-900/50 to-gray-900/70 backdrop-blur-sm border border-purple-500/30 rounded-2xl p-5 shadow-xl transform hover:scale-[1.02] transition-all duration-300 animate-fade-in"
                style={{ animationDelay: `${idx * 0.3}s`, animationFillMode: 'both' }}
              >
                {/* Position label */}
                <div className="text-center mb-4">
                  <span className="text-xs uppercase tracking-wider text-purple-400 font-semibold">
                    {getPositionLabel(sel.position)}
                  </span>
                  <p className="text-purple-500 text-xs">{getPositionDescription(sel.position)}</p>
                </div>

                {/* Rune symbol */}
                <div className="flex justify-center mb-4">
                  <div className={`
                    w-20 h-24 rounded-xl flex items-center justify-center border-2
                    ${sel.isReversed 
                      ? 'border-red-400/70 bg-red-900/20 shadow-lg shadow-red-400/20' 
                      : 'border-amber-400/70 bg-amber-900/20 shadow-lg shadow-amber-400/20'}
                    ${sel.isReversed ? 'rotate-180' : ''}
                  `}>
                    <img src={runeImg(sel.rune.id)} alt="" className="w-16 h-16 rounded-lg object-cover" />
                  </div>
                </div>

                {/* Rune name */}
                <div className="text-center mb-3">
                  <h3 className="text-amber-200 text-xl font-bold font-serif">{sel.rune.nameRu}</h3>
                  <p className="text-purple-400 text-sm italic">{sel.rune.name}</p>
                  {sel.isReversed && (
                    <span className="inline-block mt-1 px-2 py-0.5 bg-red-900/40 border border-red-500/30 rounded text-red-300 text-xs">
                      Перевёрнутая
                    </span>
                  )}
                </div>

                {/* Meaning */}
                <div className="mb-3">
                  <p className="text-purple-200 text-sm text-center italic">
                    {sel.isReversed ? sel.rune.reversedMeaning : sel.rune.meaning}
                  </p>
                </div>

                {/* Interpretation */}
                <div className="bg-purple-950/50 rounded-lg p-3 border border-purple-700/30">
                  <p className="text-purple-100 text-sm leading-relaxed">
                    {getRuneText(sel)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="bg-purple-900/30 backdrop-blur-sm border border-amber-500/30 rounded-2xl p-6 md:p-8 mb-8">
          <h2 className="text-2xl font-bold text-amber-300 font-serif text-center mb-4">
            ✦ Общее толкование ✦
          </h2>
          <div className="text-purple-100 leading-relaxed space-y-4">
            <p>
              <span className="text-amber-300 font-semibold">Прошлое ({drawnRunes[0]?.rune.nameRu}):</span>{' '}
              {getRuneText(drawnRunes[0])}
            </p>
            <p>
              <span className="text-amber-300 font-semibold">Настоящее ({drawnRunes[1]?.rune.nameRu}):</span>{' '}
              {getRuneText(drawnRunes[1])}
            </p>
            <p>
              <span className="text-amber-300 font-semibold">Будущее ({drawnRunes[2]?.rune.nameRu}):</span>{' '}
              {getRuneText(drawnRunes[2])}
            </p>
            <p className="text-center text-purple-300 italic pt-2 border-t border-purple-700/30">
              Руны указывают путь, но выбор всегда за вами. 
              Прошлое научило, настоящее даёт силу, будущее зависит от ваших решений.
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => setShowWarning(true)}
            className="px-8 py-4 bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white font-bold text-lg rounded-xl shadow-lg shadow-amber-600/30 transform hover:scale-105 transition-all duration-300 cursor-pointer"
          >
            ✦ Новое гадание ✦
          </button>
        </div>

        <p className="text-center text-purple-500 text-xs mt-8">
          Гадание на рунах Старшего Футарка • 24 руны • Расклад «Три Норны»
        </p>
      </div>

      {/* Warning Modal */}
      {showWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-gradient-to-b from-purple-900/95 to-gray-900/95 border-2 border-amber-500/50 rounded-2xl p-6 md:p-8 max-w-lg w-full shadow-2xl shadow-amber-500/20 relative">
            {/* Close button */}
            <button
              onClick={() => setShowWarning(false)}
              className="absolute top-4 right-4 text-purple-400 hover:text-amber-300 transition-colors text-2xl cursor-pointer"
            >
              ✕
            </button>

            {/* Goddess symbol */}
            <div className="text-center mb-4">
              <img src={freyaImg} alt="Фрейя" className="w-40 md:w-48 mx-auto mb-3 rounded-2xl border border-amber-500/30 shadow-lg shadow-amber-900/40" />
              <div className="text-3xl rune-symbol text-amber-400/60 mb-2">ᚠ ᚢ ᚦ</div>
              <h2 className="text-2xl md:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-yellow-300 to-amber-200 font-serif">
                Предостережение Фрейи
              </h2>
              <p className="text-purple-400 text-sm italic mt-1">Богиня ванахов, повелительница сейда</p>
            </div>

            {/* Warning text */}
            <div className="bg-purple-950/50 rounded-lg p-4 md:p-5 border border-purple-700/30 mb-6">
              <p className="text-purple-100 leading-relaxed text-center italic">
                «Остановись, смертный. Я, Фрейя, богиня любви, войны и магии, 
                владычица Фолькванга, не поощряю частое гадание.
              </p>
              <p className="text-purple-100 leading-relaxed text-center italic mt-3">
                Руны — священный дар Одина, вырезанный на мировом древе Иггдрасиль. 
                Тревожить их чаще одного раза в день — значит проявлять 
                неуважение к силам, что управляют нитями судьбы. 
                Норны не терпят суеты.»
              </p>
              <p className="text-amber-300 text-center mt-4 font-semibold">
                ✦ Вернись завтра, когда солнце взойдёт вновь ✦
              </p>
            </div>

            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => setShowWarning(false)}
                className="flex-1 px-6 py-3 bg-purple-800/50 hover:bg-purple-700/50 border border-purple-500/50 text-purple-200 font-semibold rounded-lg transition-all duration-300 cursor-pointer"
              >
                Понятно, подожду
              </button>
              <button
                onClick={() => {
                  setShowWarning(false);
                  startGame();
                }}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-amber-700 to-yellow-700 hover:from-amber-600 hover:to-yellow-600 text-white font-bold rounded-lg shadow-lg transform hover:scale-105 transition-all duration-300 cursor-pointer"
              >
                Всё равно гадать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
