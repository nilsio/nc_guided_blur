NC Guided Blur is an edge-aware blur, guided by a second image, usually the original plate (formerly GuidedMatte). Its main use is refining a rough matte: the full RGB guided filter follows colour boundaries in the guide, including edges with similar luminance.

Connect the original plate to Guide / Plate and a monochrome mask to Rough Matte. Blur Width is like a search range, and Edge Detail controls the detail frequency to include.

Based on Rafael Silva’s **rs_GuidedBlur 1.3** Nuke gizmo, which in turn was based on *Guided Image Filtering* by Kaiming He, Jian Sun and Xiaoou Tang (ECCV 2010). Big thanks to Rafael for the original tool.

Flame version by **Nils Crompton**  
Questions or bugs: **[hello@nilscrompton.com](mailto:hello@nilscrompton.com)**

**Version 0.4.** Aimed at Flame 2025.2.3 and up. Compiler checks have passed on Mac in 2025.2.3 and 2026.2.2; an earlier build also passed in 2025.2.5. Linux hasn’t been tested yet, and matching results across versions still needs a visual check.

Shared under [MIT](https://opensource.org/license/mit), with the upstream [BSD-2-Clause](https://opensource.org/license/bsd-2-clause) notices kept in the source. Commercial use and modifications are welcome—please keep the licence notices with it. The full texts are included in the GLSL files.
