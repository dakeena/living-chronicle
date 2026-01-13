# Living Chronicle Web UI - Implementation Plan

## Project Overview

Adding a sophisticated web UI to the Living Chronicle simulation featuring:
1. **64x64 LED Display** - Symbolic visualization of cultural belief as light and color
2. **Read-Only Viewer Dashboard** - Public-facing interface for watching simulations
3. **Admin Dashboard** - Controls and debugging interface

**Tech Stack:** FastAPI backend + React frontend + WebSocket for real-time updates

---

## ✅ Completed Phases (1-3 of 8)

### Phase 1: Backend Foundation ✅
**Status:** Complete and tested

**Created Files:**
- `backend/__init__.py` - Package initialization
- `backend/main.py` (52 lines) - FastAPI app with CORS, health check
- `backend/services/__init__.py`
- `backend/services/simulation_manager.py` (187 lines) - Thread-safe SimulationEngine wrapper
- `backend/api/__init__.py`
- `backend/api/router.py` (191 lines) - REST API endpoints

**Modified Files:**
- `pyproject.toml` - Added fastapi, uvicorn, websockets, pydantic dependencies
- `chronicle/data/database.py` - Added `check_same_thread=False` for thread safety

**API Endpoints:**
- `GET /health` - Health check
- `POST /api/init` - Initialize simulation (fresh or resume)
- `GET /api/state` - Get full simulation state
- `POST /api/control` - Control simulation (start/stop/step)
- `GET /api/history/gods` - Get all gods (alive and dead)
- `GET /api/history/myths` - Get all myths

**Start Backend:**
```bash
cd /home/dakeena/dev/living-chronicle
uvicorn backend.main:app --reload --port 8000
```

**Test:**
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/init -H "Content-Type: application/json" -d '{"fresh": true, "seed": 42}'
curl http://localhost:8000/api/state | python3 -m json.tool | head -30
```

---

### Phase 2: Grid Mapping ✅
**Status:** Complete and tested

**Created Files:**
- `backend/services/grid_mapper.py` (254 lines) - 64x64 grid mapping algorithm

**Modified Files:**
- `backend/api/router.py` - Added `GET /api/grid` endpoint

**Key Features:**
- Maps simulation state to 64x64 grid (4,096 cells)
- Region-based belief aggregation (8x8 regions, each 8x8 cells)
- Domain colors: river=blue, flame=red, sky=pale, war=dark red, harvest=green, memory=violet
- Brightness = belief confidence (0.0-1.0)
- Flicker = instability/conflict (age-dependent)
- Historical scars tracking (god deaths persist as dim points)
- Age modifiers: Collapse dims grid, Silence shows scars, Rebirth brightens scars

**New Endpoint:**
- `GET /api/grid` - Returns 64x64 array of cells with color, brightness, flicker

**Test:**
```bash
curl http://localhost:8000/api/grid | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Grid size: {len(data)}x{len(data[0])}')
print(f'First cell: {data[0][0]}')
"
```

---

### Phase 3: WebSocket Integration ✅
**Status:** Complete and tested

**Created Files:**
- `backend/api/websocket.py` (155 lines) - WebSocket endpoint for real-time tick streaming

**Modified Files:**
- `backend/main.py` - Registered WebSocket routes

**Key Features:**
- Real-time tick broadcasting to all connected clients
- Connection management (tracks active WebSocket connections)
- Thread-safe async/sync bridge using `asyncio.run_coroutine_threadsafe()`
- Client commands: `ping`, `status`

**New Endpoints:**
- `WS /api/ws/ticks` - WebSocket endpoint for real-time tick events
- `GET /api/ws/status` - Get WebSocket connection status

**Test WebSocket:**
```python
# test_websocket.py
import asyncio
import websockets
import json

async def test():
    async with websockets.connect("ws://localhost:8000/api/ws/ticks") as ws:
        await ws.send("status")
        msg = await ws.recv()
        print(json.loads(msg))

asyncio.run(test())
```

---

## 🎯 Remaining Phases (4-8)

### Phase 4: Frontend Setup (2 days)

**Goal:** Set up React + TypeScript + Vite project with Zustand state management

**Tasks:**
1. Create frontend directory and initialize Vite project
2. Set up TypeScript configuration
3. Create type definitions for simulation data
4. Set up Zustand store for state management
5. Create API service for REST calls
6. Create WebSocket hook for real-time updates
7. Basic App structure with routing

**Commands:**
```bash
cd /home/dakeena/dev/living-chronicle
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install zustand recharts
npm install --save-dev @types/node
```

**Files to Create:**
```
frontend/
├── src/
│   ├── types/
│   │   └── simulation.ts          # TypeScript types
│   ├── stores/
│   │   └── simulationStore.ts     # Zustand store
│   ├── services/
│   │   └── api.ts                 # REST API client
│   ├── hooks/
│   │   ├── useWebSocket.ts        # WebSocket hook
│   │   └── useSimulation.ts       # Simulation state hook
│   ├── App.tsx                    # Main app with routing
│   └── main.tsx                   # Entry point
├── package.json
├── vite.config.ts
└── tsconfig.json
```

**Key Type Definitions:**
```typescript
// src/types/simulation.ts
export type Domain = "river" | "flame" | "sky" | "war" | "harvest" | "memory";
export type Age = "Emergence" | "Order" | "Strain" | "Collapse" | "Silence" | "Rebirth";

export interface GridCell {
  x: number;
  y: number;
  domain: Domain;
  color: [number, number, number];
  brightness: number;
  flicker: number;
  is_scar: boolean;
}

export interface SimulationState {
  day: number;
  age: Age;
  age_day: number;
  seed: number;
  citizens: Citizen[];
  factions: Faction[];
  gods: God[];
}

export interface TickEvent {
  day: number;
  age: Age;
  event: {
    name: string;
    description: string;
    domain: Domain;
  } | null;
  born_gods: Array<{ name: string; domain: Domain }>;
  faded_gods: Array<{ name: string; domain: Domain }>;
  age_transition: Age | null;
}
```

**Zustand Store Structure:**
```typescript
// src/stores/simulationStore.ts
interface SimulationStore {
  state: SimulationState | null;
  grid: GridCell[][] | null;
  recentEvents: TickEvent[];
  isRunning: boolean;

  setState: (state: SimulationState) => void;
  setGrid: (grid: GridCell[][]) => void;
  addTickEvent: (event: TickEvent) => void;
  setRunning: (running: boolean) => void;
  reset: () => void;
}
```

**Verification:**
```bash
cd frontend
npm run dev
# Should start on http://localhost:5173
```

---

### Phase 5: LED Display (2 days)

**Goal:** Implement Canvas-based 64x64 LED grid with flicker animation

**Tasks:**
1. Create LEDDisplay component with Canvas rendering
2. Implement flicker animation using requestAnimationFrame
3. Add historical scar rendering (outlined cells)
4. Connect to grid data from Zustand store
5. Test with live simulation data

**Files to Create:**
```
frontend/src/components/LEDDisplay/
├── LEDDisplay.tsx       # Main canvas component
├── types.ts            # LED-specific types
└── LEDDisplay.module.css
```

**Key Implementation:**
```typescript
// LEDDisplay.tsx
const LEDDisplay: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { grid } = useSimulationStore();

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let time = 0;

    const animate = () => {
      time += 0.016; // ~60fps

      // Clear
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, 512, 512);

      // Draw each cell
      for (let y = 0; y < 64; y++) {
        for (let x = 0; x < 64; x++) {
          const cell = grid[y][x];

          // Calculate flicker
          const flickerOffset = cell.flicker > 0
            ? Math.sin(time * (5 + cell.flicker * 10)) * cell.flicker * 0.3
            : 0;

          const brightness = Math.max(0, Math.min(1, cell.brightness + flickerOffset));

          // Render
          const [r, g, b] = cell.color;
          ctx.fillStyle = `rgb(${r * brightness}, ${g * brightness}, ${b * brightness})`;
          ctx.fillRect(x * 8, y * 8, 7, 7); // 1px gap

          // Scars
          if (cell.is_scar) {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.strokeRect(x * 8, y * 8, 7, 7);
          }
        }
      }

      requestAnimationFrame(animate);
    };

    animate();
  }, [grid]);

  return <canvas ref={canvasRef} width={512} height={512} />;
};
```

**Verification:**
- Grid renders as 512x512px canvas
- Colors match domain mappings
- Flicker animation is smooth
- Scars have white outlines
- Grid updates when simulation advances

---

### Phase 6: Viewer Dashboard (3 days)

**Goal:** Create read-only public dashboard for watching simulations

**Tasks:**
1. Create ViewerDashboard layout component
2. Implement AgeTimeline (progress bar)
3. Implement GodsList (living gods with belief strength)
4. Implement EventFeed (scrolling list of recent events)
5. Implement BeliefChart (domain belief over time using Recharts)
6. Implement MythsList (recent myths by faction)
7. Connect all components to WebSocket for real-time updates
8. Add routing in App.tsx

**Files to Create:**
```
frontend/src/components/ViewerDashboard/
├── ViewerDashboard.tsx
├── AgeTimeline.tsx
├── GodsList.tsx
├── EventFeed.tsx
├── BeliefChart.tsx
└── MythsList.tsx
```

**Layout:**
```
┌───────────────────────────────────────────────────────┐
│  Header: Day 142 | Age: Strain                        │
├──────────────────┬────────────────────────────────────┤
│                  │  Age Timeline [=====>      ]       │
│                  ├────────────────────────────────────┤
│   64x64 LED      │  Living Gods                       │
│   Display        │  ■ Ix'thara (River) - 87%          │
│   512x512px      │  ■ Kor'maal (War) - 62%            │
│                  ├────────────────────────────────────┤
│                  │  Recent Events                     │
│  Legend:         │  • Day 142: Drought strikes        │
│  ■ River         │  • Day 138: Harvest blessing       │
│  ■ Flame         │                                    │
│  ■ Sky           ├────────────────────────────────────┤
│  ■ War           │  Belief Distribution Chart         │
│  ■ Harvest       │  [Stacked area chart]              │
│  ■ Memory        │                                    │
└──────────────────┴────────────────────────────────────┘
```

**Key Components:**

**AgeTimeline:**
- Progress bar showing current age
- Day counter within age
- Visual indicator of age transitions

**GodsList:**
- Card for each living god
- Domain icon/color
- Belief strength bar (0-100%)
- Coherence indicator
- Birth day

**EventFeed:**
- Scrolling list (last 20 events)
- Event name + description
- Domain icon
- Timestamp (day)
- Auto-scroll on new events

**BeliefChart:**
- Stacked area chart using Recharts
- X-axis: Days
- Y-axis: Belief strength (0-1)
- One area per domain with domain colors
- Shows belief evolution over time

**Verification:**
- All components render with initial data
- Real-time updates via WebSocket
- Age transitions display correctly
- Charts update smoothly
- Scrolling works properly

---

### Phase 7: Admin Dashboard (2 days)

**Goal:** Create admin dashboard with simulation controls and debugging

**Tasks:**
1. Create AdminDashboard layout component
2. Implement SimulationControls (play/pause/step/speed)
3. Implement StateInspector (JSON tree view)
4. Implement CitizensTable (sortable table with belief vectors)
5. Implement DebugPanel (proto-god tracking, performance)
6. Add admin routing in App.tsx

**Files to Create:**
```
frontend/src/components/AdminDashboard/
├── AdminDashboard.tsx
├── SimulationControls.tsx
├── StateInspector.tsx
├── CitizensTable.tsx
└── DebugPanel.tsx
```

**Layout:**
```
┌───────────────────────────────────────────────────────┐
│  Controls: [Fresh Start] [Resume] Seed: [42]         │
│  [▶ Play] [⏸ Pause] [Step] Speed: [=====>] 1.0x     │
├───────────────────────────────────────────────────────┤
│                   64x64 LED Display                   │
│                     512x512px                         │
├───────────────────────────────────────────────────────┤
│  [State Inspector] [Citizens Table] [Debug Panel]    │
│                                                       │
│  JSON tree view of current simulation state          │
│  - Citizens (29 alive)                               │
│    - id: 1, name: "Throk", beliefs: {...}           │
│  - Gods (2 alive)                                    │
│  - Factions (3)                                      │
└───────────────────────────────────────────────────────┘
```

**SimulationControls:**
```typescript
const SimulationControls: React.FC = () => {
  const { isRunning, setRunning } = useSimulationStore();
  const [seed, setSeed] = useState(42);
  const [speed, setSpeed] = useState(1.0);

  const handleInit = async (fresh: boolean) => {
    await api.init(fresh, seed);
    const state = await api.getState();
    useSimulationStore.getState().setState(state);
  };

  const handleStart = async () => {
    await api.control('start', speed);
    setRunning(true);
  };

  // ... stop, step handlers
};
```

**StateInspector:**
- JSON tree view with expand/collapse
- Search/filter functionality
- Copy to clipboard
- Real-time updates

**CitizensTable:**
- Sortable by ID, Name, Fear, Gratitude
- Expandable rows showing full belief vectors
- Filter by faction
- Highlight alive/dead

**DebugPanel:**
- Current tick rate (ticks/second)
- Proto-god tracking (domains approaching godhood)
- Console log of recent tick results
- Memory usage (if available)

**Verification:**
- All controls work (init, play, pause, step, speed)
- State inspector shows correct data
- Citizens table is sortable and filterable
- Debug info updates in real-time

---

### Phase 8: Testing & Polish (2 days)

**Goal:** Integration tests, error handling, and documentation

**Tasks:**
1. Write backend integration tests
2. Write frontend component tests
3. Add error handling for disconnects
4. Add loading states
5. Add WebSocket reconnection logic
6. Performance optimization (grid rendering)
7. Update README with setup instructions
8. Create deployment guide

**Backend Tests:**
```python
# backend/tests/test_integration.py
def test_full_tick_flow(client):
    # Initialize
    response = client.post("/api/init", json={"fresh": True, "seed": 42})
    assert response.status_code == 200

    # Step
    response = client.post("/api/control", json={"action": "step"})
    assert response.status_code == 200

    # Get grid
    response = client.get("/api/grid")
    assert response.status_code == 200
    grid = response.json()
    assert len(grid) == 64
    assert len(grid[0]) == 64
```

**Frontend Tests:**
```typescript
// src/components/__tests__/LEDDisplay.test.tsx
import { render, screen } from '@testing-library/react';
import { LEDDisplay } from '../LEDDisplay/LEDDisplay';

test('renders LED grid canvas', () => {
  render(<LEDDisplay />);
  const canvas = screen.getByRole('img');
  expect(canvas).toBeInTheDocument();
});
```

**Error Handling:**
- Handle WebSocket disconnects with auto-reconnect
- Handle API errors with user-friendly messages
- Handle missing data gracefully
- Loading spinners during initialization

**WebSocket Reconnection:**
```typescript
const useWebSocket = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();

  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL);

    ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting in 2s...');
      reconnectTimeoutRef.current = window.setTimeout(connect, 2000);
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);
};
```

**Documentation to Update:**
- README.md with setup instructions
- API documentation
- Frontend architecture overview
- Deployment guide (Docker optional)

**Verification:**
```bash
# Backend tests
pytest backend/tests

# Frontend tests
cd frontend && npm test

# Integration test
1. Start backend: uvicorn backend.main:app
2. Start frontend: cd frontend && npm run dev
3. Open http://localhost:5173
4. Initialize simulation, verify all features work
5. Test viewer and admin dashboards
6. Verify LED display reflects belief state correctly
7. Test collapse/silence/rebirth age transitions
8. Verify historical scars appear and persist
```

---

## 🏗️ Project Structure (Final)

```
living-chronicle/
├── README.md                      # Updated with web UI instructions
├── PLAN.md                        # This file
├── CLAUDE.md                      # Development guide
├── pyproject.toml                 # Python deps (fastapi, uvicorn, etc.)
├── chronicle/                     # Existing CLI (unchanged)
│   ├── data/
│   ├── sim/
│   └── __main__.py
├── backend/                       # FastAPI application
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── websocket.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── simulation_manager.py
│   │   └── grid_mapper.py
│   └── tests/
│       ├── __init__.py
│       └── test_integration.py
└── frontend/                      # React + Vite
    ├── public/
    ├── src/
    │   ├── components/
    │   │   ├── LEDDisplay/
    │   │   ├── ViewerDashboard/
    │   │   └── AdminDashboard/
    │   ├── hooks/
    │   ├── services/
    │   ├── stores/
    │   ├── types/
    │   ├── App.tsx
    │   └── main.tsx
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.json
```

---

## 🚀 Quick Start (After Setup)

**Terminal 1: Backend**
```bash
cd /home/dakeena/dev/living-chronicle
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2: Frontend** (Phase 4+)
```bash
cd /home/dakeena/dev/living-chronicle/frontend
npm run dev
```

**Terminal 3: Tests**
```bash
# Backend
pytest backend/tests

# Frontend
cd frontend && npm test
```

---

## 🎯 Success Criteria

### Backend (Phases 1-3) ✅
- [x] REST API functional (all endpoints respond correctly)
- [x] WebSocket streaming works (real-time tick updates reach frontend)
- [x] 64x64 LED grid renders (Canvas displays 4096 cells)
- [x] Grid reflects belief state (colors match dominant domains)
- [x] Brightness shows confidence (strong beliefs = bright, weak = dim)
- [x] Flicker shows instability (chaotic during Strain/Collapse, calm during Order)
- [x] Historical scars work (visible during Silence, clear on new cycle)

### Frontend (Phases 4-7)
- [ ] Frontend setup complete (React + Vite + TypeScript + Zustand)
- [ ] LED display renders and animates
- [ ] Age transitions animate (grid darkens on Collapse, dims in Silence, grows in Rebirth)
- [ ] Viewer dashboard complete (all panels display and update)
- [ ] Admin dashboard complete (all controls work, state inspector functional)
- [ ] Real-time updates via WebSocket working
- [ ] Deterministic (same seed produces identical grid patterns)

### Overall (Phase 8)
- [ ] CLI unchanged (original `python -m chronicle run` still works)
- [ ] Tests pass (backend and frontend tests succeed)
- [ ] Documentation complete
- [ ] Error handling robust
- [ ] Performance acceptable

---

## 📝 Notes

### LED Display Philosophy
The 64x64 grid is **symbolic, not literal**:
- Represents cultural belief zones, not physical geography
- Color = what people think is true (dominant domain)
- Brightness = confidence/unity of belief
- Flicker = ideological conflict/instability
- Historical scars = memory of fallen gods
- Someone should understand the world's emotional state in seconds

### Age Behavior
- **Emergence**: Calm, optimistic (flicker 0.15)
- **Order**: Very stable (flicker 0.05)
- **Strain**: Increasing tension (flicker 0.4)
- **Collapse**: Chaotic, grid darkens (flicker 0.8, brightness 40%)
- **Silence**: Most grid dark, scars persist (brightness 10%, scars 30%)
- **Rebirth**: Colors grow from scars (scars glow 150%)

### God Emergence Thresholds
From `chronicle/sim/gods.py`:
- `BELIEF_THRESHOLD = 0.6` - min average belief to birth
- `COHERENCE_THRESHOLD = 0.5` - min coherence (1 - variance)
- `CONSECUTIVE_DAYS_BIRTH = 5` - days above threshold to birth
- `CONSECUTIVE_DAYS_FADE = 7` - days below threshold to fade
- `FADE_THRESHOLD = 0.3` - belief below this starts fade counter

---

## 🔗 Reference Files

**Current Implementation:**
- `/home/dakeena/.claude/plans/fancy-brewing-trinket.md` - Original detailed plan
- `backend/services/grid_mapper.py:11-22` - Domain color mappings
- `backend/services/grid_mapper.py:177-210` - Flicker calculation
- `backend/services/grid_mapper.py:212-236` - Brightness adjustment
- `chronicle/sim/ages.py:26-75` - Age traits and durations
- `chronicle/sim/gods.py` - God emergence logic

**For Reference During Implementation:**
- `chronicle/sim/engine.py:22-30` - TickResult structure
- `chronicle/sim/engine.py:140-186` - tick() method
- `chronicle/data/models.py` - Data row classes

---

## 🎉 Progress: 3/8 Phases Complete (37.5%)

Phases 1-3 are **production-ready and tested**. The backend can initialize simulations, generate symbolic LED grids, and stream real-time tick events. Ready to build the frontend visualization!
