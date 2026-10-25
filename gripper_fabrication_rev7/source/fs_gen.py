"""Generate FeatureScript (Onshape) from the same CSG ops used locally. Output: LeadScrewGripper.fs"""
import numpy as np, json
import design as D
from prims import clean_loop

def f(x): return ('%.4f' % float(x)).rstrip('0').rstrip('.') if abs(float(x)) > 5e-5 else '0'
def enc_op(op, pr):
    a = '1' if op == 'add' else '0'
    if pr[0] in ('ext', 'extx'):
        lp = clean_loop(pr[1]); segs = []
        for s in lp['segs']:
            if s[0] == 'L': segs.append('[0,%s,%s]' % (f(s[1][0]), f(s[1][1])))
            else: segs.append('[1,%s,%s,%s,%s]' % (f(s[1][0]), f(s[1][1]), f(s[2][0]), f(s[2][1])))
        return '[%s,"%s",[%s,%s],[%s],%s,%s]' % (a, pr[0], f(lp['start'][0]), f(lp['start'][1]), ','.join(segs), f(pr[2]), f(pr[3]))
    if pr[0] == 'cyl':
        return '[%s,"cyl",[%s],[%s],%s]' % (a, ','.join(map(f, pr[1])), ','.join(map(f, pr[2])), f(pr[3]))
    if pr[0] == 'box':
        return '[%s,"box",[%s],[%s]]' % (a, ','.join(map(f, pr[1])), ','.join(map(f, pr[2])))
def enc_ops(ops): return '[\n        ' + ',\n        '.join(enc_op(o, p) for o, p in ops) + ']'

SPEC = [  # name, ops, pose kind, mirror?, color, material, purchased?
    ('Base', D.base(), 'ground', False, '[0.24,0.26,0.29]', D.MAT, False),
    ('Cover', D.cover(), 'ground', False, '[0.29,0.32,0.35]', D.MAT, False),
    ('Adapter ISO9409-50', D.adapter(), 'ground', False, '[0.18,0.20,0.23]', D.MAT, False),
    ('Carriage', D.carriage(), 'car', False, '[0.55,0.58,0.61]', D.MAT, False),
    ('BellCrank Lower', D.bc_plate(True), 'bc', True, '[0.79,0.80,0.82]', D.MAT, False),
    ('BellCrank Upper', D.bc_plate(False), 'bc', True, '[0.79,0.80,0.82]', D.MAT, False),
    ('FrontCrank Lower', D.fc_plate(True), 'fc', True, '[0.79,0.80,0.82]', D.MAT, False),
    ('FrontCrank Upper', D.fc_plate(False), 'fc', True, '[0.79,0.80,0.82]', D.MAT, False),
    ('ConRod', D.conrod(), 'rod', True, '[0.71,0.73,0.75]', D.MAT, False),
    ('Finger', D.finger(), 'finger', True, '[0.91,0.45,0.16]', D.MAT, False),
    ('NEMA17 linear stepper 40mm', D.motor(), 'ground', False, '[0.13,0.14,0.15]', 'STEEL', True),
    ('Tr8x%d lead screw (cut %.1fmm)' % (D.LEAD, D.SCREW_LEN), D.leadscrew(), 'ground', False, '[0.77,0.78,0.78]', 'STEEL', True),
    ('Tr8 brass flange nut', D.nut(), 'car', False, '[0.79,0.64,0.29]', 'BRASS', True),
    ('608ZZ bearing', D.bearing608(), 'ground', False, '[0.66,0.68,0.70]', 'STEEL', True),
    ('Dowel 4x36 O1', D.dowel(D.O1, 1), 'ground', True, '[0.86,0.86,0.86]', 'STEEL', True),
    ('Dowel 4x36 O2', D.dowel(D.O2, 1), 'ground', True, '[0.86,0.86,0.86]', 'STEEL', True),
    ('Shoulder screw 4x12 M3 F1', D.shoulder_screw(), 'ssF1', True, '[0.10,0.10,0.10]', 'STEEL', True),
    ('Shoulder screw 4x12 M3 F2', D.shoulder_screw(), 'ssF2', True, '[0.10,0.10,0.10]', 'STEEL', True),
    ('Shoulder screw 4x12 M3 D', D.shoulder_screw(), 'ssD', True, '[0.10,0.10,0.10]', 'STEEL', True),
    ('Shoulder screw 4x12 M3 C', D.shoulder_screw(), 'ssC', True, '[0.10,0.10,0.10]', 'STEEL', True),
] + [  # ISO 7380 button heads, appended so existing part ids (and the assembly's instances) stay put
    ({'BHS_Motor_Base': 'Button head M3x8 motor (base)', 'BHS_Motor_Cover': 'Button head M3x8 motor (cover)',
      'BHS_Cover_Wall': 'Button head M3x20 cover-wall', 'BHS_Cover_Block': 'Button head M3x20 cover-block',
      'BHS_Cover_Post': 'Button head M3x8 cover-post', 'BHS_Side_Base': 'Button head M3x8 side (base)',
      'BHS_Side_Cover': 'Button head M3x8 side (cover)', 'BHN_Nut': 'Button head M3x8 nut'}[nm],
     D.button_screw(seat, ax, ln), 'car' if frame == 'car' else 'ground', True, '[0.10,0.10,0.10]', 'STEEL', True)
    for nm, seat, ax, ln, frame in D.FASTENERS] + [  # rev 6: thrust collar, appended so existing part ids stay put
    ('Lock collar 8x14x7 (thrust)', D.collar(), 'ground', False, '[0.70,0.72,0.75]', 'STEEL', True)] + [
    # rev 7: bolt-on tip blocks, pads and their screws, appended so existing part ids stay put
    ('Tip block', D.tip_block(False), 'finger', True, '[0.91,0.45,0.16]', D.MAT, False),
    ('Pad TPU', D.pad(False), 'finger', True, '[0.12,0.12,0.13]', 'TPU', False)] + [
    ({'BHT_Tip_A': 'Button head M3x10 tip (rear)', 'BHT_Tip_B': 'Button head M3x10 tip (front)'}[nm],
     D.button_screw(seat, ax, ln), 'finger', True, '[0.10,0.10,0.10]', 'STEEL', True) for nm, seat, ax, ln in D.TIP_FASTENERS]
SPEC += [  # rev 7 (C): encoder at the screw's front end
    ('Encoder magnet puck', D.enc_puck(), 'ground', False, '[0.29,0.32,0.35]', D.MAT, False),
    ('Magnet 6x2.5 diametric', D.magnet(), 'ground', False, '[0.62,0.62,0.66]', 'STEEL', True),
    ('AS5600 encoder board', D.as5600(), 'ground', False, '[0.10,0.28,0.62]', 'FR4', True)]
SPEC += [  # rev 7 (D): controller on the cover top
    ('Protoboard 50x70', D.protoboard(), 'ground', False, '[0.16,0.42,0.22]', 'FR4', True),
    ('Standoff M3x10 rear', D.standoff(D.CTRL_C[0] - D.CTRL_HOLE[0]), 'ground', True, '[0.80,0.70,0.35]', 'BRASS', True),
    ('Standoff M3x10 front', D.standoff(D.CTRL_C[0] + D.CTRL_HOLE[0]), 'ground', True, '[0.80,0.70,0.35]', 'BRASS', True),
    ('Raspberry Pi Pico', D.pico(), 'ground', False, '[0.10,0.45,0.20]', 'FR4', True),
    ('TMC2209 driver', D.tmc2209(), 'ground', False, '[0.50,0.12,0.55]', 'FR4', True),
    ('Buck 5V MP1584', D.buck(), 'ground', False, '[0.12,0.22,0.55]', 'FR4', True)]
SPEC += [  # rev 7.1 (review item 3): bronze sleeves bonded into the cover hold the dowel tops
    ('Bushing 4x6x6 O1', D.sleeve(D.O1), 'ground', True, '[0.72,0.55,0.30]', 'BRASS', True),
    ('Bushing 4x6x6 O2', D.sleeve(D.O2), 'ground', True, '[0.72,0.55,0.30]', 'BRASS', True)]
STAND = [  # rev 7 (F): bench stand, built when the dialog's "Include bench stand" is on
    ('Stand head bracket', D.stand_bracket(), 'ground', False, '[0.24,0.26,0.29]', D.MAT, False),
    ('Stand base', D.stand_base(), 'ground', False, '[0.24,0.26,0.29]', D.MAT, False),
    ('Extrusion 2020 x 400', D.column(), 'ground', False, '[0.76,0.77,0.79]', 'ALU', True),
    ('LiPo 3S 650mAh', D.battery(), 'ground', False, '[0.16,0.16,0.18]', 'LIPO', True)]
SPEC += STAND
WIDE = {'Tip block': D.tip_block(True), 'Pad TPU': D.pad(True)}   # ops used when the dialog's tip set is Wide
consts = dict(L=D.L, R=D.r, LR=D.l, YC=D.YC, O1X=D.O1[0], O1Y=D.O1[1], O2X=D.O2[0], O2Y=D.O2[1],
              THC=np.degrees(D.TH_C), GAPMAX=D.GAP_MAX, RHO=D.MAT_RHO, WOFS=D.WIDE_OFS)

mcs = []
for s, sfx in ((1, ' U'), (-1, ' L')):
    for owner, key in (('Base', 'O1'), ('BellCrank Lower' + sfx, 'O1'), ('Base', 'O2'), ('FrontCrank Lower' + sfx, 'O2'),
                       ('BellCrank Lower' + sfx, 'F1'), ('Finger' + sfx, 'F1'), ('FrontCrank Lower' + sfx, 'F2'), ('Finger' + sfx, 'F2'),
                       ('BellCrank Lower' + sfx, 'D'), ('ConRod' + sfx, 'D'), ('Carriage', 'C'), ('ConRod' + sfx, 'C')):
        mcs.append('["%s", "%s", %d]' % (owner, key, s))
mcs += ['["Base", "SL", 0]', '["Carriage", "SL", 0]']
MCS = '[\n        ' + ',\n        '.join(mcs) + ']'
parts_src = []
for k, (nm, ops, kind, mir, col, mat, pur) in enumerate(SPEC):
    parts_src.append('    { "name" : "%s", "kind" : "%s", "mirror" : %s, "color" : %s, "mat" : "%s", "purchased" : %s,%s\n      "ops" : %s%s }'
                     % (nm, kind, 'true' if mir else 'false', col, mat, 'true' if pur else 'false',
                        ' "stand" : true,' if nm in [s[0] for s in STAND] else '', enc_ops(ops),
                        (',\n      "opsW" : ' + enc_ops(WIDE[nm])) if nm in WIDE else ''))

FS = r'''FeatureScript 3083;
import(path : "onshape/std/common.fs", version : "3083.0");

// Lead-screw parallel gripper - generated from the verified local model (fs_gen.py). Units: mm.
// One feature builds every printed and purchased part at the jaw gap chosen in the dialog.
// Kinematics: parallelogram fingers + 90 deg bell crank + conrod to lead-screw carriage (see design report).

const GAP_BOUNDS = { (millimeter) : [0, 30, %(GAPMAX)s] } as LengthBoundSpec;

export enum TipSet
{
    annotation { "Name" : "Narrow (gap 0-66 mm)" }
    NARROW,
    annotation { "Name" : "Wide (gap 20-86 mm)" }
    WIDE
}

annotation { "Feature Type Name" : "Lead Screw Gripper", "Feature Type Description" : "Builds the full gripper at a given jaw gap" }
export const leadScrewGripper = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Jaw gap (narrow tips)" }
        isLength(definition.gap, GAP_BOUNDS);
        annotation { "Name" : "Tip set", "Default" : TipSet.NARROW }
        definition.tipSet is TipSet;
        annotation { "Name" : "Include purchased parts", "Default" : true }
        definition.purchased is boolean;
        annotation { "Name" : "Include bench stand", "Default" : true }
        definition.stand is boolean;
    }
    {
        const kin = gripperKinematics(definition.gap / millimeter);
        const wide = definition.tipSet == TipSet.WIDE;
        const parts = partSpecs();
        var bodies = {};
        for (var k = 0; k < size(parts); k += 1)
        {
            const p = parts[k];
            if ((p.purchased && !definition.purchased) || (p.stand == true && !definition.stand))
                continue;
            const pid = id + ("p" ~ k);
            const body = buildPart(context, pid, (wide && p.opsW != undefined) ? p.opsW : p.ops);
            const T = poseTransform(p.kind, kin);
            opTransform(context, id + ("t" ~ k), { "bodies" : body, "transform" : T });
            dressPart(context, body, p.mirror ? p.name ~ " U" : p.name, p);
            bodies[p.mirror ? p.name ~ " U" : p.name] = body;
            if (p.mirror)
            {
                opPattern(context, id + ("m" ~ k), {
                        "entities" : body,
                        "transforms" : [mirrorAcross(plane(vector(0, 0, 0) * millimeter, vector(0, 1, 0)))],
                        "instanceNames" : ["L"] });
                const mbody = qBodyType(qCreatedBy(id + ("m" ~ k), EntityType.BODY), BodyType.SOLID);
                dressPart(context, mbody, p.name ~ " L", p);
                bodies[p.name ~ " L"] = mbody;
            }
        }
        // Named mate connectors at every pivot (z = 10.25) and on the screw axis (slider), for assembly mates
        const mcs = mateConnectorSpecs();
        for (var j = 0; j < size(mcs); j += 1)
        {
            const m = mcs[j];
            var origin = vector(kin.C[0], 0, 10.25) * millimeter;
            var xAx = vector(0, 1, 0);
            var zAx = vector(1, 0, 0);
            if (m[1] != "SL")
            {
                const pt = kin[m[1]];
                origin = vector(pt[0], m[2] * pt[1], 10.25) * millimeter;
                xAx = vector(1, 0, 0);
                zAx = vector(0, 0, 1);
            }
            opMateConnector(context, id + ("mc" ~ j), { "coordSystem" : coordSystem(origin, xAx, zAx), "owner" : bodies[m[0]] });
            setProperty(context, { "entities" : qCreatedBy(id + ("mc" ~ j), EntityType.BODY), "propertyType" : PropertyType.NAME,
                        "value" : "MC " ~ m[1] ~ (m[2] > 0 ? " U " : (m[2] < 0 ? " L " : " ")) ~ m[0] });
        }
        // true pad-to-pad gap for the chosen tip set (the wide faces sit %(WOFS)s mm further out per side)
        const faceGap = definition.gap / millimeter + (wide ? 2 * %(WOFS)s : 0);
        reportFeatureInfo(context, id, "Pad-to-pad gap: " ~ roundToPrecision(faceGap, 1) ~ " mm (" ~ (wide ? "wide" : "narrow") ~ " tips)");
    }, { "gap" : 30 * millimeter, "tipSet" : TipSet.NARROW, "purchased" : true, "stand" : true });

function mateConnectorSpecs() returns array
{
    return %(MCS)s;
}

function dressPart(context is Context, q is Query, name is string, p is map)
{
    setProperty(context, { "entities" : q, "propertyType" : PropertyType.NAME, "value" : name });
    setProperty(context, { "entities" : q, "propertyType" : PropertyType.APPEARANCE, "value" : color(p.color[0], p.color[1], p.color[2]) });
    var dens = %(RHO)s;
    if (p.mat == "STEEL")
        dens = 7.85;
    if (p.mat == "BRASS")
        dens = 8.5;
    if (p.mat == "TPU")
        dens = 1.21;
    if (p.mat == "FR4")
        dens = 1.85;
    if (p.mat == "ALU")
        dens = 2.7;
    if (p.mat == "LIPO")
        dens = 1.8;
    setProperty(context, { "entities" : q, "propertyType" : PropertyType.MATERIAL, "value" : material(p.mat, dens * gram / centimeter ^ 3) });
}

function gripperKinematics(gap is number) returns map
{
    const L = %(L)s;
    const R = %(R)s;
    const LR = %(LR)s;
    const YC = %(YC)s;
    const O1 = [%(O1X)s, %(O1Y)s];
    const O2 = [%(O2X)s, %(O2Y)s];
    const th = asin(gap / (2 * L) + sin(%(THC)s * degree));
    const ph = th - 90 * degree;
    const Dx = O1[0] + R * cos(ph);
    const Dy = O1[1] + R * sin(ph);
    const w = sqrt(LR * LR - (YC - Dy) * (YC - Dy));
    const Cx = Dx - w;
    return { "th" : th, "O1" : O1, "O2" : O2, "F1" : [O1[0] + L * cos(th), O1[1] + L * sin(th)],
            "F2" : [O2[0] + L * cos(th), O2[1] + L * sin(th)], "D" : [Dx, Dy], "C" : [Cx, YC],
            "rod" : atan2(Dy - YC, Dx - Cx) };
}

function poseTransform(kind is string, kin is map) returns Transform
{
    const zl = line(vector(0, 0, 0) * millimeter, vector(0, 0, 1));
    if (kind == "bc")
        return transform(vector(kin.O1[0], kin.O1[1], 0) * millimeter) * rotationAround(zl, kin.th);
    if (kind == "fc")
        return transform(vector(kin.O2[0], kin.O2[1], 0) * millimeter) * rotationAround(zl, kin.th);
    if (kind == "rod")
        return transform(vector(kin.C[0], kin.C[1], 0) * millimeter) * rotationAround(zl, kin.rod);
    if (kind == "finger" || kind == "ssF1")
        return transform(vector(kin.F1[0], kin.F1[1], 0) * millimeter);
    if (kind == "ssF2")
        return transform(vector(kin.F2[0], kin.F2[1], 0) * millimeter);
    if (kind == "ssD")
        return transform(vector(kin.D[0], kin.D[1], 0) * millimeter);
    if (kind == "ssC")
        return transform(vector(kin.C[0], kin.C[1], 0) * millimeter);
    if (kind == "car")
        return transform(vector(kin.C[0], 0, 0) * millimeter);
    return identityTransform();
}

function buildPart(context is Context, pid is Id, ops is array) returns Query
{
    for (var k = 0; k < size(ops); k += 1)
    {
        const op = ops[k];
        const oid = pid + ("o" ~ k);
        makePrim(context, oid, op);
        const tool = qBodyType(qCreatedBy(oid, EntityType.BODY), BodyType.SOLID);
        if (k == 0)
            continue;
        const others = qSubtraction(qBodyType(qCreatedBy(pid, EntityType.BODY), BodyType.SOLID), tool);
        if (op[0] == 1)
        {
            opBoolean(context, pid + ("b" ~ k), { "tools" : qUnion([others, tool]), "operationType" : BooleanOperationType.UNION });
        }
        else
        {
            try silent
            {
                opBoolean(context, pid + ("b" ~ k), { "tools" : tool, "targets" : others, "operationType" : BooleanOperationType.SUBTRACTION });
            }
            try silent
            {
                opDeleteBodies(context, pid + ("d" ~ k), { "entities" : qBodyType(qCreatedBy(oid, EntityType.BODY), BodyType.SOLID) });
            }
        }
    }
    return qBodyType(qCreatedBy(pid, EntityType.BODY), BodyType.SOLID);
}

function makePrim(context is Context, oid is Id, op is array)
{
    const t = op[1];
    if (t == "ext" || t == "extx")
    {
        const a = op[4];
        const b = op[5];
        var pl = plane(vector(0, 0, a) * millimeter, vector(0, 0, 1), vector(1, 0, 0));
        if (t == "extx")
            pl = plane(vector(a, 0, 0) * millimeter, vector(1, 0, 0), vector(0, 1, 0));
        const sk = newSketchOnPlane(context, oid + "sk", { "sketchPlane" : pl });
        var cur = op[2];
        const segs = op[3];
        for (var i = 0; i < size(segs); i += 1)
        {
            const s = segs[i];
            if (s[0] == 0)
            {
                skLineSegment(sk, "e" ~ i, { "start" : vector(cur[0], cur[1]) * millimeter, "end" : vector(s[1], s[2]) * millimeter });
                cur = [s[1], s[2]];
            }
            else
            {
                skArc(sk, "e" ~ i, { "start" : vector(cur[0], cur[1]) * millimeter, "mid" : vector(s[1], s[2]) * millimeter,
                            "end" : vector(s[3], s[4]) * millimeter });
                cur = [s[3], s[4]];
            }
        }
        skSolve(sk);
        opExtrude(context, oid + "ex", { "entities" : qSketchRegion(oid + "sk"), "direction" : pl.normal,
                    "endBound" : BoundingType.BLIND, "endDepth" : (b - a) * millimeter });
        opDeleteBodies(context, oid + "del", { "entities" : qCreatedBy(oid + "sk", EntityType.BODY) });
    }
    else if (t == "cyl")
    {
        fCylinder(context, oid + "c", { "bottomCenter" : vector(op[2]) * millimeter, "topCenter" : vector(op[3]) * millimeter,
                    "radius" : op[4] * millimeter });
    }
    else if (t == "box")
    {
        fCuboid(context, oid + "c", { "corner1" : vector(op[2]) * millimeter, "corner2" : vector(op[3]) * millimeter });
    }
}

function partSpecs() returns array
{
    return [
%(PARTS)s
    ];
}
''' % dict(PARTS=',\n'.join(parts_src), MCS=MCS, **{k: f(v) for k, v in consts.items()})
open('LeadScrewGripper.fs', 'w').write(FS)
open('../onshape/LeadScrewGripper.fs', 'w').write(FS)   # the copy pasted into Onshape Feature Studio 1; always identical to source/
print('bytes', len(FS), 'lines', FS.count('\n'), 'parts', len(SPEC), 'ops', sum(len(s[1]) for s in SPEC))
