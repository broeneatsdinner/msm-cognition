# Plant Island Breeding Structure captures — 2026-07-09

Raw positive-example screenshots for Breeding Structure recognition.

These images are unannotated screenshots. They are intended for detector training, comparison, and sidecar annotation. Do not draw boxes, labels, or markup directly onto these image files.

## Purpose

This set captures the normal Breeding Structure in multiple real in-game conditions:

- full island / world-view context
- zoomed idle state
- zoomed in-use state
- animation-frame variation
- parent eggs visible
- progress bar visible
- animated steam visible in some frames

## Stable recognition features

The detector should learn stable Breeding Structure features:

- forked wooden structure
- two upper egg pedestals
- central trunk and hollow opening
- translucent bowl
- lower nest/base platform
- vine and flower frame
- rock base
- rough vertical symmetry

## Variable / optional features

The detector should not require these to match exactly:

- pink steam puffs
- exact heart shape or highlight
- translucent bowl reflections
- parent egg appearance
- progress bar
- ambient island animations

## Image notes

- `plant-breeding-structure-idle-zoom-01.png` is the cleanest idle positive.
- `plant-breeding-structure-in-use-zoom-01.png` is the cleanest in-use positive.
- `plant-breeding-structure-in-use-zoom-steam-08.png` shows visible steam animation.
- overview images are useful for world-view scale and clutter/context testing.

Annotations should be stored separately in JSON, not burned into the images.
