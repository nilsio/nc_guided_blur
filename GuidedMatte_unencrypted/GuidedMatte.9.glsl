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
uniform sampler2D adsk_results_pass5;
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
