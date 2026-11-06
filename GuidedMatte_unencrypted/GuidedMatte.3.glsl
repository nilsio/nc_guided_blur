/*
Guided Matte — Matchbox implementation by Nils Crompton
Contact: hello@nilscrompton.com
New contributions: MIT. Applicable upstream material: BSD-2-Clause.

MIT License

Copyright (c) 2026 Nils Crompton

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Upstream attribution and BSD-2-Clause notice

Rafael Silva — rs_GuidedBlur v1.3 (Nuke gizmo)
www.rafael.ai — rafael@rafael.ai
https://www.nukepedia.com/tools/gizmos/filter/guided-blur-refine-edge/

The supplied gizmo credits Rafael Silva and was inspected as an implementation
reference. Nukepedia's published terms assign downloaded files the FreeBSD
(BSD-2-Clause) licence unless otherwise stated:
https://www.nukepedia.com/terms-of-use/
No different licence or separate copyright notice was found in the supplied
file or public gizmo description. The following upstream terms are retained
for applicable upstream material; the MIT grant covers the new contributions
and does not replace those terms. Rafael's original Nuke file is not bundled.

BSD 2-Clause License
https://opensource.org/license/bsd-2-clause

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

Algorithm reference: Kaiming He, Jian Sun and Xiaoou Tang,
Guided Image Filtering, ECCV 2010. This citation credits the method; it does
not purport to license the paper or any separate reference implementation.
*/
#version 120
uniform float adsk_result_w, adsk_result_h;
vec2 pixelSize() { return 1.0 / vec2(adsk_result_w, adsk_result_h); }
vec2 safeUV(vec2 uv) { return clamp(uv, 0.5 * pixelSize(), 1.0 - 0.5 * pixelSize()); }
uniform sampler2D guideTex;
uniform float blurSize;
// Integrate a box of width blurSize across pixel footprints. Width <= 1 is identity.
float boxWeight(int offset) {
    float halfWidth = 0.5 * clamp(blurSize, 1.0, 256.0);
    float x = float(offset);
    return max(0.0, min(x + 0.5, halfWidth) - max(x - 0.5, -halfWidth));
}

void main() {
    vec2 center = gl_FragCoord.xy * pixelSize();
    vec4 sum = vec4(0.0);
    float total = 0.0;
    int extent = int(ceil(0.5 * clamp(blurSize, 1.0, 256.0)));
    for (int k = -extent; k <= extent; ++k) {
        float w = boxWeight(k);
        vec2 uv = safeUV(center + vec2(float(k), 0.0) * pixelSize());
        vec3 i = texture2D(guideTex, uv).rgb;
        
        sum += w * vec4(i.r*i.g, i.r*i.b, i.g*i.b, 0.0);
        total += w;
    }
    gl_FragColor = sum / total;
}
