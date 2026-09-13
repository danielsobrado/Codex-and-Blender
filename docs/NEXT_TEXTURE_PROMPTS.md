# Optional texture upgrades

Both upgrades below have now been supplied and integrated: `canopy_branch_atlas_new.png` and `tropical_bark_basecolor.png`. No additional images are required for the current 32-asset kit. The prompts are retained for provenance and optional future variants.

## Canopy branches

Filename: `canopy_branch_atlas_new.png`. Generate at 2048 × 2048; optimize a copy to 1024 × 1024 for the current web scene.

> Create a photorealistic tropical foliage texture atlas with four different leafy branch clusters in a strict 2 × 2 grid. Each cluster contains 40–70 small, overlapping, oval leaves on thin branching brown twigs. Use irregular outlines and natural gaps, dark forest green leaves with subtle olive highlights, fine veins, and varied leaf angles. Keep each cluster entirely inside its cell with generous transparent padding. True transparent background, no checkerboard, no ground, no cast shadows, no text. Flat neutral lighting suitable for a game base-color texture.

## Tropical broadleaf bark

Filename: `tropical_bark_basecolor.png`. Generate at 2048 × 2048; optimize a copy to 1024 × 1024 for the current web scene.

> Create a seamless, tileable photorealistic base-color texture of a mature tropical broadleaf tree’s bark. Dark warm gray-brown bark, fine vertical fissures, uneven shallow ridges, scattered muted olive moss and pale gray-green lichen. Flat orthographic surface scan, uniform diffuse lighting, no directional shadows or highlights. No trunk silhouette, roots, leaves, palm rings, text, or borders. All four edges must tile seamlessly.

Check actual alpha and edge tiling before replacing materials: generated images can include a painted checkerboard or mismatched edges despite the prompt. New broadleaf bark should apply to canopy trees and shrubs; retain the original palm bark for palms.
