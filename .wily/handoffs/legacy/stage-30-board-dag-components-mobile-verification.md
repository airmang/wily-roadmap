# Stage 30 Board DAG Components Mobile Verification

## 2026-05-18T05:14:05Z - Baseline

Working directory: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend`

| Command | Exit | Evidence |
| --- | ---: | --- |
| `npm ls @xyflow/react framer-motion cmdk @radix-ui/react-dialog @radix-ui/react-tooltip @radix-ui/react-progress @dagrejs/dagre --depth=0` | 0 | `@dagrejs/dagre@3.0.0`, `@radix-ui/react-progress@1.1.8`, React Flow, cmdk, dialog, tooltip, framer-motion present. |
| `node -e "const p=require('./package.json'); console.log(p.dependencies['@tremor/react'] || 'absent')"` | 0 | Output: `absent`. |
| `npm run lint` | 0 | ESLint completed with no reported errors. |
| `npm run build` | 0 | Next.js 15.5.18 production build compiled, type-checked, generated routes, and exited 0. |

## 2026-05-18T05:41:31Z - Final

Working directory: `/Users/wilycastle/Code/projects/wily-plugin/wily-board`

| Command | Exit | Evidence |
| --- | ---: | --- |
| `cd frontend && npm run lint` | 0 | ESLint completed with no reported errors. |
| `cd frontend && npm run build` | 0 | Next.js 15.5.18 production build compiled, type-checked, generated 7 static pages, and exited 0. |
| `uv run pytest` | 0 | 76 passed, 14 warnings in 2.53s. |
| Playwright desktop smoke, `1280x900` | 0 | `stageNodes: 4`, React Flow `display: block`, mobile list hidden, rail visible, headline and Attention text present. Screenshot: `/tmp/stage30-desktop-final.png`. |
| Playwright mobile smoke, `375x812` | 0 | React Flow `display: none`, mobile list `display: block`, `mobileRows: 4`, rail hidden, Local Desk bottom sheet contains Working and Up Next. Screenshot: `/tmp/stage30-mobile-final.png`. |
| Playwright repo switcher smoke | 0 | Shared and Personal headings present, repos loaded, pinned star count `1`. Screenshot: `/tmp/stage30-switcher-final.png`. |

Notes:
- A transient `npm run build` failure occurred while the Next dev server was still using `.next`; stopping the dev server and rerunning the same build produced a clean pass.
- Integration reviewer findings were fixed before the final verification pass.
