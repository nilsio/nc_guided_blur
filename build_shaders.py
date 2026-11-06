"""Generate an RGB guided-filter Matchbox using legacy portable GLSL."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'matchbox'
OUT.mkdir(exist_ok=True)
HEADER = '/*\nNC Guided Blur — Matchbox implementation by Nils Crompton\nContact: hello@nilscrompton.com\nNew contributions: MIT. Applicable upstream material: BSD-2-Clause.\n\nMIT License\n\nCopyright (c) 2026 Nils Crompton\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n\nUpstream attribution and BSD-2-Clause notice\n\nRafael Silva — rs_GuidedBlur v1.3 (Nuke gizmo)\nwww.rafael.ai — rafael@rafael.ai\nhttps://www.nukepedia.com/tools/gizmos/filter/guided-blur-refine-edge/\n\nThe supplied gizmo credits Rafael Silva and was inspected as an implementation\nreference. Nukepedia\'s published terms assign downloaded files the FreeBSD\n(BSD-2-Clause) licence unless otherwise stated:\nhttps://www.nukepedia.com/terms-of-use/\nNo different licence or separate copyright notice was found in the supplied\nfile or public gizmo description. The following upstream terms are retained\nfor applicable upstream material; the MIT grant covers the new contributions\nand does not replace those terms. Rafael\'s original Nuke file is not bundled.\n\nBSD 2-Clause License\nhttps://opensource.org/license/bsd-2-clause\n\nRedistribution and use in source and binary forms, with or without\nmodification, are permitted provided that the following conditions are met:\n\n1. Redistributions of source code must retain the above copyright notice,\n   this list of conditions and the following disclaimer.\n\n2. Redistributions in binary form must reproduce the above copyright notice,\n   this list of conditions and the following disclaimer in the documentation\n   and/or other materials provided with the distribution.\n\nTHIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"\nAND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE\nIMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE\nARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE\nLIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR\nCONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF\nSUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS\nINTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN\nCONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)\nARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE\nPOSSIBILITY OF SUCH DAMAGE.\n\nAlgorithm reference: Kaiming He, Jian Sun and Xiaoou Tang,\nGuided Image Filtering, ECCV 2010. This citation credits the method; it does\nnot purport to license the paper or any separate reference implementation.\n*/\n#version 120\nuniform float adsk_result_w, adsk_result_h;\n'
COORDS = '''vec2 pixelSize() { return 1.0 / vec2(adsk_result_w, adsk_result_h); }
vec2 safeUV(vec2 uv) { return clamp(uv, 0.5 * pixelSize(), 1.0 - 0.5 * pixelSize()); }
'''
KERNEL = '''uniform float blurSize;
// Integrate a box of width blurSize across pixel footprints. Width <= 1 is identity.
float boxWeight(int offset) {
    float halfWidth = 0.5 * clamp(blurSize, 1.0, 256.0);
    float x = float(offset);
    return max(0.0, min(x + 0.5, halfWidth) - max(x - 0.5, -halfWidth));
}
'''
INPUTS = '''uniform sampler2D guideTex;
uniform sampler2D matteTex;
float readMatte(vec2 uv) {
    return texture2D(matteTex, safeUV(uv)).r;
}
'''

def write(n, body):
    (OUT / f'nc_guided_blur.{n}.glsl').write_text(HEADER + COORDS + body)

# Four horizontal moment passes: mean RGB + matte, square RGB, cross RGB, RGB*matte.
for n, expression in enumerate(('vec4(i, p)', 'vec4(i * i, 0.0)',
                                'vec4(i.r*i.g, i.r*i.b, i.g*i.b, 0.0)',
                                'vec4(i * p, 0.0)'), 1):
    inputs = INPUTS if n in (1, 4) else 'uniform sampler2D guideTex;\n'
    p = 'float p = readMatte(uv);' if n in (1, 4) else ''
    write(n, inputs + KERNEL + f'''
void main() {{
    vec2 center = gl_FragCoord.xy * pixelSize();
    vec4 sum = vec4(0.0);
    float total = 0.0;
    int extent = int(ceil(0.5 * clamp(blurSize, 1.0, 256.0)));
    for (int k = -extent; k <= extent; ++k) {{
        float w = boxWeight(k);
        vec2 uv = safeUV(center + vec2(float(k), 0.0) * pixelSize());
        vec3 i = texture2D(guideTex, uv).rgb;
        {p}
        sum += w * {expression};
        total += w;
    }}
    gl_FragColor = sum / total;
}}
''')

def blur(n, src, axis):
    write(n, f'uniform sampler2D adsk_results_pass{src};\n' + KERNEL + f'''
void main() {{
    vec2 center = gl_FragCoord.xy * pixelSize();
    vec4 sum = vec4(0.0);
    float total = 0.0;
    int extent = int(ceil(0.5 * clamp(blurSize, 1.0, 256.0)));
    for (int k = -extent; k <= extent; ++k) {{
        float w = boxWeight(k);
        vec2 uv = safeUV(center + {axis} * pixelSize());
        sum += w * texture2D(adsk_results_pass{src}, uv);
        total += w;
    }}
    gl_FragColor = sum / total;
}}
''')

for n in range(1, 5):
    blur(n + 4, n, 'vec2(0.0, float(k))')

write(9, '''uniform sampler2D adsk_results_pass5;
uniform sampler2D adsk_results_pass6;
uniform sampler2D adsk_results_pass7;
uniform sampler2D adsk_results_pass8;
uniform float edgeDetail;
void main() {
    vec2 uv = safeUV(gl_FragCoord.xy * pixelSize());
    vec4 mean = texture2D(adsk_results_pass5, uv);
    vec3 diag = texture2D(adsk_results_pass6, uv).rgb - mean.rgb * mean.rgb;
    vec3 off = texture2D(adsk_results_pass7, uv).rgb
             - vec3(mean.r*mean.g, mean.r*mean.b, mean.g*mean.b);
    vec3 cov = texture2D(adsk_results_pass8, uv).rgb - mean.rgb * mean.a;
    float eps = pow(10.0, -clamp(edgeDetail, 0.0, 6.0));
    diag = max(diag, vec3(0.0)) + vec3(eps);
    // Solve (covariance + eps Identity) a = cov(I,p) using Cholesky.
    // Equivalent to the gizmo's cofactor inverse, with positive pivot protection.
    float floorPivot = max(eps * 0.0001, 1.0e-12);
    float l00 = sqrt(max(diag.r, floorPivot));
    float l10 = off.r / l00;
    float l20 = off.g / l00;
    float l11 = sqrt(max(diag.g - l10*l10, floorPivot));
    float l21 = (off.b - l20*l10) / l11;
    float l22 = sqrt(max(diag.b - l20*l20 - l21*l21, floorPivot));
    float y0 = cov.r / l00;
    float y1 = (cov.g - l10*y0) / l11;
    float y2 = (cov.b - l20*y0 - l21*y1) / l22;
    vec3 a;
    a.b = y2 / l22;
    a.g = (y1 - l21*a.b) / l11;
    a.r = (y0 - l10*a.g - l20*a.b) / l00;
    float b = mean.a - dot(a, mean.rgb);
    gl_FragColor = vec4(a, b);
}
''')
blur(10, 9, 'vec2(float(k), 0.0)')
write(11, INPUTS + KERNEL + '''uniform sampler2D adsk_results_pass10;
uniform float mixAmount;
uniform bool clampMatte;
void main() {
    vec2 center = safeUV(gl_FragCoord.xy * pixelSize());
    vec4 sum = vec4(0.0);
    float total = 0.0;
    int extent = int(ceil(0.5 * clamp(blurSize, 1.0, 256.0)));
    for (int k = -extent; k <= extent; ++k) {
        float w = boxWeight(k);
        vec2 uv = safeUV(center + vec2(0.0, float(k)) * pixelSize());
        sum += w * texture2D(adsk_results_pass10, uv);
        total += w;
    }
    vec4 ab = sum / total;
    vec3 guide = texture2D(guideTex, center).rgb;
    float p = readMatte(center);
    float q = dot(ab.rgb, guide) + ab.a;
    if (clampMatte) q = clamp(q, 0.0, 1.0);
    q = mix(p, q, clamp(mixAmount, 0.0, 1.0));
    if (blurSize <= 1.0 || mixAmount <= 0.0) q = p;
    gl_FragColor = vec4(guide, q);
}
''')

root = ET.Element('ShaderNodePreset', {
    'Name': 'NC Guided Blur', 'ShaderType': 'Matchbox', 'Version': '0.4', 'SoftwareVersion': '2025.2.3', 'CommercialUsePermitted': 'True',
    'Description': 'NC Guided Blur refines a rough matte using colour detail from a guide image, usually the original plate. The full RGB guided filter follows colour boundaries, including edges with similar luminance.\n\nConnect the original plate to Guide / Plate and a monochrome mask to Rough Matte. Blur Width is like a search range, and Edge Detail controls the detail frequency to include.\n\nBased on Rafael Silva’s **rs_GuidedBlur 1.3** Nuke gizmo, which in turn was based on *Guided Image Filtering* by Kaiming He, Jian Sun and Xiaoou Tang (ECCV 2010). Big thanks to Rafael for the original tool.\n\nFlame version by **Nils Crompton**  \nQuestions or bugs: **[hello@nilscrompton.com](mailto:hello@nilscrompton.com)**\n\n**Version 0.4.** Aimed at Flame 2025.2.3 and up. Compiler checks have passed on Mac in 2025.2.3 and 2026.2.2; an earlier build also passed in 2025.2.5. Linux hasn’t been tested yet, and matching results across versions still needs a visual check.\n\nShared under [MIT](https://opensource.org/license/mit), with the upstream [BSD-2-Clause](https://opensource.org/license/bsd-2-clause) notices kept in the source. Commercial use and modifications are welcome—please keep the licence notices with it. The full texts are included in the GLSL files.',
    'MatteProvider': 'True', 'SupportsAction': 'False', 'SupportsTimeline': 'False',
    'SupportsTransition': 'False', 'SupportsAdaptiveDegradation': 'False',
    'LimitInputsToTexture': 'True', 'TimelineUseBack': 'False'})
controls = {
    'blurSize': ('Blur Width', '30.0', '1.0', '256.0', '0.1', '0', '0', 'Box width in output pixels. Nuke size mapping needs image comparison.'),
    'edgeDetail': ('Edge Detail', '3.5', '0.0', '6.0', '0.05', '1', '0', 'Epsilon = 10^(-detail), as in rs_GuidedBlur. Higher values preserve finer edges and grain.'),
    'mixAmount': ('Mix', '1.0', '0.0', '1.0', '0.01', '2', '0', 'Blend original and refined matte.'),
    'clampMatte': ('Clamp Matte', 'False', None, None, None, '0', '1', 'Clamp refined matte to 0-1 before mixing. Off matches the unclamped Nuke graph.'),
}
seen = set()
for n in range(1, 12):
    shader = ET.SubElement(root, 'Shader', Index=str(n), OutputBitDepth='Float16' if n == 11 else 'Float32')
    source = (OUT / f'nc_guided_blur.{n}.glsl').read_text()
    for typ, name in re.findall(r'uniform (sampler2D|float|bool) (\w+)\s*;', source):
        if name.startswith('adsk_') and typ != 'sampler2D':
            continue
        u = ET.SubElement(shader, 'Uniform', Type=typ, Name=name)
        if name in seen and not name.startswith('adsk_'):
            ET.SubElement(u, 'Duplicate')
            continue
        seen.add(name)
        if typ == 'sampler2D':
            u.attrib.update({'Mipmaps': 'False', 'GL_TEXTURE_WRAP_S': 'GL_CLAMP_TO_EDGE',
                'GL_TEXTURE_WRAP_T': 'GL_CLAMP_TO_EDGE', 'GL_TEXTURE_MIN_FILTER': 'GL_NEAREST',
                'GL_TEXTURE_MAG_FILTER': 'GL_NEAREST'})
            if not name.startswith('adsk_'):
                guide = name == 'guideTex'
                u.attrib.update({'Index': '0' if guide else '1', 'NoInput': 'Error',
                    'InputType': 'Front' if guide else 'Matte',
                    'DisplayName': 'Guide / Plate' if guide else 'Rough Matte'})
        else:
            label, default, lo, hi, inc, row, col, tip = controls[name]
            u.attrib.update({'DisplayName': label, 'Default': default, 'Row': row,
                'Col': col, 'Page': '0', 'Tooltip': tip})
            if lo is not None:
                u.attrib.update({'Min': lo, 'Max': hi, 'Inc': inc, 'ResDependent': 'None'})
page = ET.SubElement(root, 'Page', Name='NC Guided Blur', Page='0')
for i, title in enumerate(('Refinement', 'Output')):
    ET.SubElement(page, 'Col', Name=title, Col=str(i), Page='0')
ET.indent(root)
ET.ElementTree(root).write(OUT / 'nc_guided_blur.xml', encoding='utf-8', xml_declaration=True)
print(f'Generated 11 shader passes and XML in {OUT}')
