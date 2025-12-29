# ChatGPT 3D Rendering Prompt - Big Hex

**Create a photorealistic 3D rendering of a large 3DOF hexapod walking robot with a standard Coca-Cola can placed next to it for scale reference.**

## Robot Specifications

### Body Configuration
- **Shape:** Hexagonal platform, approximately 400mm across (flat-to-flat), 6mm thick
- **Material appearance:** Dark gray PETG 3D-printed plastic with subtle layer lines
- **Two-plate design:** Top and bottom plates separated by ~25mm aluminum standoffs
- **Electronics visible:** Raspberry Pi, wiring, battery pack between plates

### Leg Arrangement (6 legs, viewed from above)
```
        FRONT (0°)
    L1           R1    (mounted at 330° and 30°)
    L2 -------- R2     (mounted at 270° and 90°, sides)
    L3           R3    (mounted at 210° and 150°)
        REAR (180°)
```

### Leg Specifications (each leg has 3 segments)
1. **Coxa (hip joint):** 50mm length, dark gray bracket housing a 40×20×40mm servo, rotates horizontally
2. **Femur (upper leg):** 100mm length, medium gray reinforced beam with servo mounted at coxa end
3. **Tibia (lower leg):** 150mm length, light gray tapered structural beam (20mm at servo end, tapering to 10mm at foot)
4. **Foot tip:** 25mm black rubber/TPU dome tip for grip

### Servo Details (LX-16A)
- **18× identical servos** (40×20×40.5mm, full metal gear, black aluminum case)
- All servos are the same size (unlike small hexapod)
- Silver metal output shaft on each servo
- Visible daisy-chain cables (thin 3-wire) running through each leg
- Red/black power wires, white signal wire

### Pose (standing position)
- Standing height: ~120mm from body underside to ground
- Legs splayed outward in stable stance
- **Tripod stance:** Legs L1, R2, L3 slightly forward; R1, L2, R3 slightly back
- Tibias angled down approximately 50° from horizontal
- Femurs angled slightly upward (~20° from horizontal)
- Coxa joints rotated ~30° outward from body

### Scale Reference - Coca-Cola Can
- **Standard 330ml Coke can** placed on the ground next to the robot
- Can dimensions: 122mm tall × 66mm diameter
- Position: Front-right of the hexapod, about 100mm away
- The robot body should be approximately **3× the width of the can**
- The robot's standing height should be approximately **equal to the can height**

### Electronics (visible between body plates)
- **Raspberry Pi Zero 2W** (65×30mm green PCB) mounted centrally
- **2S LiPo battery** (rectangular, ~140×45×25mm, blue shrink wrap with warning labels)
- **Buck converter module** (small blue PCB)
- **Wiring harness** - 6 bundles of cables going to each leg
- Zip ties organizing cables

### Materials & Colors
- Body plates: Matte dark gray PETG plastic
- Coxa brackets: Dark gray PETG
- Femur links: Medium gray PETG, thicker/beefier than small hex
- Tibia links: Light gray PETG, tapered beam profile
- Foot tips: Black TPU rubber domes
- Servos: Black anodized aluminum cases with silver shafts
- Wires: Black/red power, white signal cables
- Standoffs: Silver aluminum hex standoffs

### Size Comparison Guide
```
Component              Size        vs Coke Can (122mm tall, 66mm wide)
─────────────────────────────────────────────────────────────────────
Body width             400mm       ~6× can diameter
Body plate thickness   6mm         ~5% of can height
Leg total length       300mm       ~2.5× can height
Standing height        120mm       ~1× can height (eye level with can)
Servo size             40mm        ~60% of can diameter
Femur length           100mm       ~80% of can height
Tibia length           150mm       ~1.2× can height
```

### Lighting & Environment
- **Studio lighting:** Soft key light from upper left, fill from right
- **Background:** Clean white/light gray gradient, slightly darker at edges
- **Ground surface:** Smooth matte gray surface with subtle reflection
- **Shadows:** Soft shadows under robot and can, not harsh

### Camera Angle
- **3/4 front-top view** (approximately 30° above horizontal, 30° from front)
- Robot and Coke can both fully visible
- Slight depth of field blur on background
- Robot is the hero, can is clearly for scale reference

### Style Notes
- Photorealistic render quality
- Industrial/maker aesthetic - this is a serious robotics project, not a toy
- Visible mechanical details: screws, servo horns, wire routing
- The robot should look **substantial and capable** compared to the can
- Clean but functional - some visible wires add authenticity
- Metal servo cases should have subtle reflections

### Key Visual Points
1. Robot body is **3× wider** than the Coke can
2. Robot stands at **same height** as the can (~120mm)
3. Each leg is **longer than the can is tall**
4. Servos are **larger than a thumb** (40mm)
5. Overall impression: "This is a serious walking robot, not a desk toy"

---

## Alternative Prompt (Shorter Version)

> Create a photorealistic 3D render of a large hexapod robot (6-legged walker) with a Coca-Cola can next to it for scale. The robot has a 400mm wide dark gray hexagonal body, six 3-jointed legs with 40mm black aluminum servos at each joint, and stands about 120mm tall (same height as the can). Each leg has: 50mm coxa, 100mm femur, 150mm tibia segments in gray 3D-printed plastic with black rubber feet. Show it in a studio setting with soft lighting, 3/4 view from front-above. The robot body should be about 3× the width of the Coke can, emphasizing its substantial size. Include visible electronics (Raspberry Pi, blue LiPo battery) between the body plates and thin cables daisy-chaining through each leg.
