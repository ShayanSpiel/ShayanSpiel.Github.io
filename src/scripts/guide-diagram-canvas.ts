type Side = "top" | "right" | "bottom" | "left" | "center";
type Anchor = { side: Side; ratio?: number };
type Point = { x: number; y: number };
type Edge = {
  id: string;
  from: string;
  to: string;
  fromAnchor?: Anchor;
  toAnchor?: Anchor;
  controlPoints?: [Point, Point];
  waypoints?: Point[];
  routing?: "curve" | "orthogonal";
  tone?: "primary" | "destructive";
  bend?: number;
  dashed?: boolean;
  arrow?: boolean;
};

const diagrams = [...document.querySelectorAll<HTMLElement>("[data-guide-diagram]")];

const readPoint = (rect: DOMRect, canvas: DOMRect, side: Side, ratio = 0.5): Point => {
  const xRatio = Math.max(0, Math.min(1, ratio));
  let x = rect.left + rect.width * 0.5;
  let y = rect.top + rect.height * 0.5;
  if (side === "top" || side === "bottom" || side === "center") x = rect.left + rect.width * xRatio;
  if (side === "left" || side === "right") y = rect.top + rect.height * xRatio;
  if (side === "top") y = rect.top;
  if (side === "right") x = rect.right;
  if (side === "bottom") y = rect.bottom;
  if (side === "left") x = rect.left;
  return { x: x - canvas.left, y: y - canvas.top };
};

const toDesign = (point: Point, canvas: DOMRect, width: number, height: number): Point => ({
  x: (point.x / canvas.width) * width,
  y: (point.y / canvas.height) * height,
});

const mirrorSide = (side: Side): Side => {
  if (side === "left") return "right";
  if (side === "right") return "left";
  return side;
};

/**
 * The Persian deck mirrors its node layout, so connector semantics must mirror
 * with it. DOMRects already report the nodes' new physical positions; this
 * transforms only the authored English-side anchors and control points. Without
 * it, top/bottom anchor ratios remain attached to the opposite slot and the
 * resulting paths cross through the whole diagram.
 */
const mirrorEdge = (edge: Edge): Edge => {
  const mirrorAnchor = (anchor?: Anchor): Anchor | undefined => anchor && ({
    side: mirrorSide(anchor.side),
    ratio: anchor.ratio === undefined || anchor.side === "left" || anchor.side === "right"
      ? anchor.ratio
      : 1 - anchor.ratio,
  });
  return {
    ...edge,
    fromAnchor: mirrorAnchor(edge.fromAnchor),
    toAnchor: mirrorAnchor(edge.toAnchor),
    controlPoints: edge.controlPoints?.map(point => ({ x: 1 - point.x, y: point.y })) as [Point, Point] | undefined,
    waypoints: edge.waypoints?.map(point => ({ x: 1 - point.x, y: point.y })),
  };
};

const setPath = (path: SVGPathElement, edge: Edge, from: Point, to: Point, width: number, height: number) => {
  const snapOddStroke = (point: Point): Point => ({ x: Math.round(point.x) + .5, y: Math.round(point.y) + .5 });
  if (edge.routing === "orthogonal" && edge.waypoints?.length) {
    const vertices = edge.waypoints.map(point => ({ x: point.x * width, y: point.y * height }));
    const first = vertices[0];
    const last = vertices[vertices.length - 1];
    if (edge.fromAnchor?.side === "left" || edge.fromAnchor?.side === "right") first.y = from.y;
    if (edge.fromAnchor?.side === "top" || edge.fromAnchor?.side === "bottom") first.x = from.x;
    if (edge.toAnchor?.side === "left" || edge.toAnchor?.side === "right") last.y = to.y;
    if (edge.toAnchor?.side === "top" || edge.toAnchor?.side === "bottom") last.x = to.x;
    path.setAttribute("d", [from, ...vertices, to].map(snapOddStroke).map((point, index) => `${index ? "L" : "M"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" "));
    return;
  }
  const controls = edge.controlPoints?.map(point => ({ x: point.x * width, y: point.y * height })) as [Point, Point] | undefined;
  if (controls) {
    path.setAttribute("d", `M ${from.x.toFixed(2)} ${from.y.toFixed(2)} C ${controls[0].x.toFixed(2)} ${controls[0].y.toFixed(2)} ${controls[1].x.toFixed(2)} ${controls[1].y.toFixed(2)} ${to.x.toFixed(2)} ${to.y.toFixed(2)}`);
    return;
  }
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  // Every connection is a measured cubic: the first and last handles stay
  // on the source/target side of the edge, while the horizontal delta is
  // distributed across the curve. This prevents the old fixed-canvas
  // handles from looping through cards when a row is resized or reflowed.
  const bend = Math.max(-0.35, Math.min(0.35, edge.bend ?? 0));
  const travel = Math.max(18, Math.abs(dy) * 0.38);
  const c1x = from.x + dx * 0.18;
  const c2x = to.x - dx * 0.18;
  const c1y = from.y + dy * 0.46 + bend * height * 0.08;
  const c2y = to.y - dy * 0.38 + bend * height * 0.04;
  // Straight connectors stay straight. Purely vertical runs (a rail through
  // its dots) and horizontal peer-to-peer arrows (card → card rails) read as
  // broken zig-zags when the measured cubic adds a decorative bow, so they
  // render as exact lines. Annotation journeys keep their authored bend.
  const vertical = Math.abs(dx) < 1;
  if (vertical || (!bend && Math.abs(dy) < travel)) {
    const crispFrom = snapOddStroke(from);
    const crispTo = snapOddStroke(to);
    const line = vertical
      ? `M ${crispFrom.x.toFixed(2)} ${crispFrom.y.toFixed(2)} L ${crispFrom.x.toFixed(2)} ${crispTo.y.toFixed(2)}`
      : `M ${crispFrom.x.toFixed(2)} ${crispFrom.y.toFixed(2)} L ${crispTo.x.toFixed(2)} ${crispTo.y.toFixed(2)}`;
    path.setAttribute("d", line);
    return;
  }
  // Keep a small, measured bow on nearly level journeys. Previously this
  // branch discarded `bend`, flattening annotations such as the files note
  // into a straight line and hiding their arrowheads against card borders.
  if (Math.abs(dy) < travel) {
    const direction = dy >= 0 ? 1 : -1;
    const arc = bend * height * 0.12;
    path.setAttribute("d", `M ${from.x.toFixed(2)} ${from.y.toFixed(2)} C ${c1x.toFixed(2)} ${(from.y + direction * travel + arc).toFixed(2)} ${c2x.toFixed(2)} ${(to.y - direction * travel + arc).toFixed(2)} ${to.x.toFixed(2)} ${to.y.toFixed(2)}`);
    return;
  }
  path.setAttribute("d", `M ${from.x.toFixed(2)} ${from.y.toFixed(2)} C ${c1x.toFixed(2)} ${c1y.toFixed(2)} ${c2x.toFixed(2)} ${c2y.toFixed(2)} ${to.x.toFixed(2)} ${to.y.toFixed(2)}`);
};

const placeProblemMergeNode = (root: HTMLElement) => {
  const merge = root.querySelector<HTMLElement>('[data-guide-node="merge"]');
  const statement = root.querySelector<HTMLElement>('[data-guide-node="statement"]');
  if (!merge || !statement || !root.classList.contains("guide-problem__body")) return;
  const bodyRect = root.getBoundingClientRect();
  const statementRect = statement.getBoundingClientRect();
  const inputRight = Math.max(
    ...["logo", "colors", "fonts", "guidelines", "templates"]
      .map(id => root.querySelector<HTMLElement>(`[data-guide-node="${id}"]`)?.getBoundingClientRect().right ?? bodyRect.left),
  );
  const gap = Math.max(24, statementRect.left - inputRight);
  merge.style.left = `${((inputRight + gap * 0.5 - bodyRect.left) / bodyRect.width) * 100}%`;
  merge.style.top = "52%";
};

const updateDiagram = (root: HTMLElement) => {
  const canvas = root.getBoundingClientRect();
  const width = Number(root.dataset.guideDesignWidth || 0);
  const height = Number(root.dataset.guideDesignHeight || 0);
  if (!canvas.width || !canvas.height || !width || !height) return;

  placeProblemMergeNode(root);

  let edges: Edge[] = [];
  try { edges = JSON.parse(root.dataset.guideEdges || "[]") as Edge[]; } catch { return; }
  const node = (id: string) => root.querySelector<HTMLElement>(`[data-guide-node="${id}"]`);
  const nodeIds = new Set([...root.querySelectorAll<HTMLElement>("[data-guide-node]")].map(item => item.dataset.guideNode));
  root.dataset.guideGeometryValid = String(edges.every(edge => nodeIds.has(edge.from) && nodeIds.has(edge.to)));
  edges.forEach(edge => {
    const directionalEdge = document.documentElement.dir === "rtl" ? mirrorEdge(edge) : edge;
    const path = root.querySelector<SVGPathElement>(`[data-guide-edge="${edge.id}"]`);
    const fromNode = node(edge.from);
    const toNode = node(edge.to);
    if (!path || !fromNode || !toNode) return;
    const fromAnchor = directionalEdge.fromAnchor || { side: "center" as Side };
    const toAnchor = directionalEdge.toAnchor || { side: "center" as Side };
    // Edge anchors inside file cards are semantic markers, not the visual
    // endpoint. Resolve their side against the owning card so connectors
    // begin/end at the card perimeter instead of disappearing through its
    // content. Other node types intentionally keep their own bounds.
    const visualRect = (element: HTMLElement) => element.matches(".guide-file-card__edge-anchor")
      ? (element.closest<HTMLElement>(".guide-file-card")?.getBoundingClientRect() || element.getBoundingClientRect())
      : element.getBoundingClientRect();
    const from = toDesign(readPoint(visualRect(fromNode), canvas, fromAnchor.side, fromAnchor.ratio), canvas, width, height);
    const to = toDesign(readPoint(visualRect(toNode), canvas, toAnchor.side, toAnchor.ratio), canvas, width, height);
    // Leave a small, consistent visual gap before left-facing arrow targets.
    // The marker tip otherwise lands underneath the target card's border and
    // reads as a missing arrow at presentation scale.
    if (directionalEdge.arrow && toAnchor.side === "left") to.x = Math.max(0, to.x - 10);
    if (directionalEdge.arrow && toAnchor.side === "right") to.x = Math.min(width, to.x + 10);
    setPath(path, directionalEdge, from, to, width, height);
    path.classList.toggle("is-dashed", Boolean(edge.dashed));
    path.classList.toggle("has-arrow", Boolean(edge.arrow));
    path.setAttribute("data-guide-edge-from", edge.from);
    path.setAttribute("data-guide-edge-to", edge.to);
    if (edge.arrow) {
      const markerId = root.dataset.guideMarkerId;
      if (markerId) path.style.markerEnd = `url(#${markerId}-${directionalEdge.tone || "primary"})`;
    } else {
      path.style.removeProperty("marker-end");
    }
  });
  root.dataset.guideGeometryResolved = "true";
  if (root.hasAttribute("data-reference-scene")) root.dataset.referenceGeometryResolved = "true";
};

diagrams.forEach(root => {
  const observer = new ResizeObserver(() => requestAnimationFrame(() => updateDiagram(root)));
  observer.observe(root);
  root.querySelectorAll<HTMLElement>("[data-guide-node]").forEach(node => observer.observe(node));
  addEventListener("resize", () => updateDiagram(root), { passive: true });
  addEventListener("brand-guide:refresh-diagrams", () => updateDiagram(root));
  requestAnimationFrame(() => updateDiagram(root));
});
