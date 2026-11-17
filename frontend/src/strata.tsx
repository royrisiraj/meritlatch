// Decorative geometry only. No timers, pointer tracking, data or authority.
export function BrandMark() {
  return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 2.5 20.5 7.25v9.5L12 21.5l-8.5-4.75v-9.5Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" /><path d="M12 2.5V12m0 0 8.5-4.75M12 12 3.5 7.25" stroke="currentColor" strokeWidth="1.4" /><circle cx="12" cy="12" r="2" fill="currentColor" /></svg>;
}

export function GeometricMesh() {
  const nodes = Array.from({ length:26 }, (_, i) => ({x:40+((i*137)%620), y:40+((i*193)%820)}));
  return <svg className="geometric-mesh" viewBox="0 0 700 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
    <g className="mesh-lines">{nodes.flatMap((a,i)=>nodes.slice(i+1).map((b,j)=>Math.hypot(a.x-b.x,a.y-b.y)<225 ? <line key={`${i}-${j}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y} /> : null))}</g>
    <g className="mesh-nodes">{nodes.map((n,i)=><circle key={i} cx={n.x} cy={n.y} r={i%5===0?3:1.7} />)}</g>
    <path className="mesh-plane" d="M150 600 350 480 550 600 350 720Z" />
    <path className="mesh-plane" d="M150 570 350 450 550 570 350 690Z" />
    <path className="mesh-plane" d="M150 540 350 420 550 540 350 660Z" />
  </svg>;
}
