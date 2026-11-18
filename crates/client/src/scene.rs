use crate::{Bridge, Options, RenderReport};
use bevy::{
    anti_alias::fxaa::Fxaa,
    asset::{LoadState, RenderAssetUsages},
    camera::visibility::NoFrustumCulling,
    core_pipeline::tonemapping::Tonemapping,
    gltf::GltfMaterialName,
    mesh::{Indices, PrimitiveTopology},
    platform::time::Instant,
    prelude::*,
    window::PrimaryWindow,
    world_serialization::WorldInstanceReady,
};
use tc_session::{ARENA_METERS, TICK_MS, Timing, VIEW_STRIDE};

const COLORS: [Color; 2] = [Color::srgb(0.12, 0.69, 1.0), Color::srgb(1.0, 0.38, 0.11)];
const CLIPS: [&str; 3] = ["idle", "move", "fire"];
const JOINTS: [&str; 3] = ["head", "thigh.L", "recoil"];

#[derive(Resource)]
pub(crate) struct ExitAfterReport(pub bool);

#[derive(Resource, Default)]
pub(crate) struct Battle {
    loaded: bool,
    initialized: bool,
    tick: u32,
    since_view: f32,
    applied: u32,
    frame_ms: Vec<f64>,
    update_ms: Vec<f64>,
    queue_ms: Vec<f64>,
    inspected_joints: [Option<Entity>; 3],
    last_pose: Option<[Transform; 3]>,
}

#[derive(Resource)]
pub(crate) struct Rivet(Handle<Gltf>);

#[derive(Resource)]
pub(crate) struct RigAssets {
    scene: Handle<WorldAsset>,
    team_color: [Option<Handle<StandardMaterial>>; 2],
    graph: Handle<AnimationGraph>,
    clips: [AnimationNodeIndex; 3],
}

#[derive(Component)]
pub(crate) struct CameraOrbit;

#[derive(Component)]
pub(crate) struct UnitVisual {
    id: usize,
    player: usize,
    from: Vec3,
    to: Vec3,
    heading: u8,
    clip: usize,
}

#[derive(Component)]
pub(crate) struct Rig {
    player: usize,
    animator: Option<Entity>,
    playing: Option<usize>,
}

#[derive(Resource)]
pub(crate) struct Synthetic {
    mesh: Handle<Mesh>,
    colors: [Handle<StandardMaterial>; 2],
}

pub(crate) fn setup(
    mut commands: Commands,
    options: Res<Options>,
    server: Res<AssetServer>,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,
) {
    commands.spawn((
        Camera3d::default(),
        Projection::Perspective(PerspectiveProjection {
            fov: 42_f32.to_radians(),
            ..default()
        }),
        Tonemapping::None,
        Msaa::Off,
        Fxaa::default(),
        CameraOrbit,
        Transform::from_xyz(0.0, 175.0, 115.0).looking_at(Vec3::ZERO, Vec3::Y),
    ));
    commands.spawn((
        DirectionalLight {
            illuminance: 7800.0,
            shadow_maps_enabled: false,
            ..default()
        },
        Transform::from_xyz(-6.0, 10.0, 6.0).looking_at(Vec3::ZERO, Vec3::Y),
    ));
    commands.spawn((
        Mesh3d(meshes.add(terrain())),
        MeshMaterial3d(materials.add(StandardMaterial {
            perceptual_roughness: 1.0,
            ..default()
        })),
    ));
    if options.inspect {
        let pad = meshes.add(Cylinder::new(2.1, 0.04));
        for (player, x) in [-2.3, 2.3].into_iter().enumerate() {
            commands.spawn((
                Mesh3d(pad.clone()),
                MeshMaterial3d(materials.add(StandardMaterial {
                    base_color: COLORS[player].with_alpha(1.0).mix(&Color::BLACK, 0.82),
                    perceptual_roughness: 0.88,
                    ..default()
                })),
                Transform::from_xyz(x, 0.018, 0.0),
            ));
        }
    }

    let mut chassis =
        Mesh::from(Cuboid::new(1.28, 0.42, 1.76)).translated_by(Vec3::new(0., 0.22, 0.));
    let turret = Mesh::from(Cuboid::new(0.68, 0.44, 0.86)).translated_by(Vec3::new(0., 0.6, 0.21));
    let barrel = Mesh::from(Cuboid::new(0.18, 0.19, 0.58)).translated_by(Vec3::new(0., 0.58, 0.72));
    chassis
        .merge(&turret)
        .expect("cuboid mesh attributes match");
    chassis
        .merge(&barrel)
        .expect("cuboid mesh attributes match");
    commands.insert_resource(Synthetic {
        mesh: meshes.add(chassis),
        colors: COLORS.map(|color| {
            materials.add(StandardMaterial {
                base_color: color,
                perceptual_roughness: 0.76,
                ..default()
            })
        }),
    });
    if options.rigs > 0 || options.inspect {
        commands.insert_resource(Rivet(server.load("rivet.glb")));
    }
}

fn terrain() -> Mesh {
    // A flat survey grid shares the simulation's ground plane and scale.
    const DIVISIONS: usize = 64;
    let points = DIVISIONS + 1;
    let mut positions = Vec::with_capacity(points * points);
    let mut colors = Vec::with_capacity(points * points);
    for z in 0..points {
        for x in 0..points {
            let px = (x as f32 / DIVISIONS as f32 - 0.5) * ARENA_METERS;
            let pz = (z as f32 / DIVISIONS as f32 - 0.5) * ARENA_METERS;
            positions.push([px, 0.0, pz]);
            let noise = (((x * 83 + z * 167) ^ (x * z * 13)) % 17) as f32 * 0.0017;
            let grid = if x % 8 == 0 || z % 8 == 0 { 0.012 } else { 0.0 };
            let strip = if (30..=34).contains(&x) { 0.018 } else { 0.0 };
            let brightness = noise + grid + strip;
            colors.push([
                0.040 + brightness,
                0.056 + brightness,
                0.062 + brightness,
                1.0,
            ]);
        }
    }
    let mut indices = Vec::with_capacity(DIVISIONS * DIVISIONS * 6);
    for z in 0..DIVISIONS {
        for x in 0..DIVISIONS {
            let i = (z * points + x) as u32;
            let next = i + points as u32;
            indices.extend_from_slice(&[i, next, i + 1, i + 1, next, next + 1]);
        }
    }
    let normals = vec![[0., 1., 0.]; positions.len()];
    Mesh::new(
        PrimitiveTopology::TriangleList,
        RenderAssetUsages::default(),
    )
    .with_inserted_attribute(Mesh::ATTRIBUTE_POSITION, positions)
    .with_inserted_attribute(Mesh::ATTRIBUTE_NORMAL, normals)
    .with_inserted_attribute(Mesh::ATTRIBUTE_COLOR, colors)
    .with_inserted_indices(Indices::U32(indices))
}

pub(crate) fn prepare_rigs(
    mut commands: Commands,
    bridge: Res<Bridge>,
    rig: Option<Res<Rivet>>,
    server: Res<AssetServer>,
    gltfs: Res<Assets<Gltf>>,
    mut graphs: ResMut<Assets<AnimationGraph>>,
    existing: Option<Res<RigAssets>>,
) {
    let Some(rig) = rig else { return };
    if existing.is_some() || bridge.state.lock().unwrap().status.error.is_some() {
        return;
    }
    if let Some(LoadState::Failed(error)) = server.get_load_state(&rig.0) {
        bridge.state.lock().unwrap().status.error = Some(format!("Rivet failed to load ({error})"));
        return;
    }
    if !server.is_loaded_with_dependencies(&rig.0) {
        return;
    }

    let gltf = gltfs.get(&rig.0).expect("loaded GLB");
    let assets = (|| {
        let scene = gltf.default_scene.clone()?;
        gltf.named_materials.get("PlayerColor")?;
        let [Some(idle), Some(movement), Some(fire)] =
            CLIPS.map(|name| gltf.named_animations.get(name).cloned())
        else {
            return None;
        };
        let (graph, nodes) = AnimationGraph::from_clips([idle, movement, fire]);
        let clips = nodes.try_into().ok()?;
        Some(RigAssets {
            scene,
            team_color: [None, None],
            graph: graphs.add(graph),
            clips,
        })
    })();

    match assets {
        Some(assets) => commands.insert_resource(assets),
        None => {
            bridge.state.lock().unwrap().status.error = Some(
                "Rivet GLB must contain its default scene, PlayerColor and all three clips".into(),
            );
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn rig_ready(
    event: On<WorldInstanceReady>,
    mut commands: Commands,
    bridge: Res<Bridge>,
    options: Res<Options>,
    mut assets: ResMut<RigAssets>,
    children: Query<&Children>,
    names: Query<&Name>,
    mut rigs: Query<&mut Rig>,
    mut players: Query<&mut AnimationPlayer>,
    mut materials: Query<(
        &mut MeshMaterial3d<StandardMaterial>,
        Option<&GltfMaterialName>,
    )>,
    mut battle: ResMut<Battle>,
    mut finish: ResMut<Assets<StandardMaterial>>,
) {
    let root = event.entity;
    let Ok(mut rig) = rigs.get_mut(root) else {
        return;
    };
    let mut color_regions = 0;
    for child in children.iter_descendants(root) {
        // Independent draw bounds for skinned primitives can exclude an animated limb.
        if let Ok((mut material, name)) = materials.get_mut(child) {
            commands.entity(child).insert(NoFrustumCulling);
            if name.is_some_and(|name| name.0 == "PlayerColor") {
                let slot = &mut assets.team_color[rig.player];
                if slot.is_none()
                    && let Some(original) = finish.get(&material.0).cloned()
                {
                    *slot = Some(finish.add(StandardMaterial {
                        base_color: COLORS[rig.player],
                        ..original
                    }));
                }
                if let Some(color) = slot {
                    material.0 = color.clone();
                    color_regions += 1;
                }
            }
        }
        if let Ok(mut animation) = players.get_mut(child) {
            animation.play(assets.clips[0]).repeat();
            commands
                .entity(child)
                .insert(AnimationGraphHandle(assets.graph.clone()));
            rig.animator = Some(child);
            rig.playing = Some(0);
        }
        if options.inspect
            && rig.player == 0
            && let Ok(name) = names.get(child)
        {
            for (joint, expected) in battle.inspected_joints.iter_mut().zip(JOINTS) {
                if name.as_str() == expected {
                    *joint = Some(child);
                }
            }
        }
    }
    let mut shared = bridge.state.lock().unwrap();
    if rig.animator.is_some() && color_regions > 0 {
        shared.status.rigs_ready += 1;
        shared.status.colored_rigs[rig.player] += 1;
    } else {
        shared.status.error =
            Some("Rivet instance has no animation player or PlayerColor primitive".into());
    }
}

fn spawn_battle(
    commands: &mut Commands,
    options: &Options,
    synthetic: &Synthetic,
    rigs: Option<&RigAssets>,
) {
    let count = if options.inspect { 2 } else { options.units };
    for id in 0..count {
        let team_size = count / 2;
        let player = id / team_size;
        let has_rig = options.inspect || id % team_size < options.rigs / 2;
        let position = if options.inspect {
            Vec3::new(if player == 0 { -2.3 } else { 2.3 }, 0.039, 0.)
        } else {
            Vec3::new(0., -10.0, 0.)
        };
        let heading = if options.inspect {
            0
        } else if player == 0 {
            2
        } else {
            6
        };
        let mut entity = commands.spawn((
            UnitVisual {
                id,
                player,
                from: position,
                to: position,
                heading,
                clip: 0,
            },
            Transform::from_translation(position),
        ));
        if has_rig {
            entity
                .insert((
                    WorldAssetRoot(rigs.expect("loaded rigs").scene.clone()),
                    Rig {
                        player,
                        animator: None,
                        playing: None,
                    },
                ))
                .observe(rig_ready);
        } else {
            entity.insert((
                Mesh3d(synthetic.mesh.clone()),
                MeshMaterial3d(synthetic.colors[player].clone()),
            ));
        }
    }
}

#[allow(clippy::too_many_arguments, clippy::type_complexity)]
pub(crate) fn update(
    mut commands: Commands,
    options: Res<Options>,
    bridge: Res<Bridge>,
    synthetic: Res<Synthetic>,
    assets: Option<Res<RigAssets>>,
    exit: Res<ExitAfterReport>,
    time: Res<Time<Real>>,
    input: Res<ButtonInput<KeyCode>>,
    window: Single<&Window, With<PrimaryWindow>>,
    mut transforms: ParamSet<(
        Single<&mut Transform, With<CameraOrbit>>,
        Query<(&mut UnitVisual, &mut Transform, Option<&mut Rig>)>,
        Query<&Transform>,
    )>,
    mut animations: Query<&mut AnimationPlayer>,
    mut battle: ResMut<Battle>,
    mut app_exit: MessageWriter<AppExit>,
) {
    let update_start = Instant::now();
    let rig_count = if options.inspect { 2 } else { options.rigs };
    let elapsed = time.elapsed_secs();
    **transforms.p0() = if options.inspect {
        Transform::from_xyz(0.6, 4.8, 11.5).looking_at(Vec3::new(0., 1.10, 0.), Vec3::Y)
    } else {
        let sweep = elapsed * 0.1;
        Transform::from_xyz(sweep.sin() * 44.0, 169.0, 112.0 + sweep.cos() * 12.0)
            .looking_at(Vec3::ZERO, Vec3::Y)
    };

    if bridge.state.lock().unwrap().status.error.is_some() {
        if !cfg!(target_arch = "wasm32") {
            app_exit.write(AppExit::error());
        }
        return;
    }
    if options.inspect && exit.0 && elapsed > 60.0 {
        bridge.state.lock().unwrap().status.error =
            Some("Rivet animation inspection timed out".into());
        return;
    }
    if !battle.initialized {
        if rig_count == 0 || assets.is_some() {
            spawn_battle(&mut commands, &options, &synthetic, assets.as_deref());
            battle.initialized = true;
        }
        return;
    }
    if !battle.loaded {
        let mut shared = bridge.state.lock().unwrap();
        if shared.status.rigs_ready == rig_count && shared.status.error.is_none() {
            shared.status.ready = true;
            battle.loaded = true;
        }
        return;
    }

    let (view, selected_clip) = {
        let mut shared = bridge.state.lock().unwrap();
        (shared.view.take(), shared.selected_clip)
    };
    let measuring = options.ticks != 0 && battle.tick > options.warmup;
    battle.since_view += time.delta_secs();
    let mut slide = (battle.since_view / (TICK_MS as f32 / 1000.0)).min(1.0);
    if let Some(view) = &view {
        battle.applied += u32::from(view.tick > options.warmup);
        battle.tick = view.tick;
        battle.since_view = 0.0;
        slide = if battle.applied == 0 && view.tick <= 1 {
            1.0
        } else {
            0.0
        };
        if options.ticks != 0 && view.tick > options.warmup {
            battle
                .queue_ms
                .push(view.queued.elapsed().as_secs_f64() * 1000.0);
        }
    }
    if options.inspect {
        for (index, key) in [
            KeyCode::Digit1,
            KeyCode::Digit2,
            KeyCode::Digit3,
            KeyCode::Digit4,
        ]
        .into_iter()
        .enumerate()
        {
            if input.just_pressed(key) {
                bridge.select_clip((index < 3).then_some(index));
            }
        }
    }
    let active_clip = selected_clip.unwrap_or((elapsed / 3.0) as usize % CLIPS.len());

    let headings: [Quat; 8] = std::array::from_fn(|heading| {
        Quat::from_rotation_y(heading as f32 * std::f32::consts::FRAC_PI_4)
    });
    for (mut unit, mut transform, rig) in &mut transforms.p1() {
        if let Some(view) = &view {
            let offset = unit.id * VIEW_STRIDE;
            let record = &view.bytes[offset..offset + VIEW_STRIDE];
            debug_assert_eq!(usize::from(record[9]), unit.player);
            let x = i32::from_le_bytes(record[..4].try_into().unwrap()) as f32 * 0.001;
            let z = i32::from_le_bytes(record[4..8].try_into().unwrap()) as f32 * 0.001;
            unit.to = Vec3::new(x, 0., z);
            unit.from = if transform.translation.y < 0.0 {
                unit.to
            } else {
                transform.translation
            };
            unit.heading = record[8];
            unit.clip = usize::from(record[10]);
        } else if options.inspect {
            unit.clip = active_clip;
        }

        let translation = unit.from.lerp(unit.to, slide);
        let rotation = headings[usize::from(unit.heading)];
        if transform.translation != translation || transform.rotation != rotation {
            transform.translation = translation;
            transform.rotation = rotation;
        }

        if let Some(mut rig) = rig
            && rig.playing != Some(unit.clip)
            && let Some(animator) = rig.animator
            && let Ok(mut animation) = animations.get_mut(animator)
            && let Some(assets) = &assets
        {
            animation.stop_all().play(assets.clips[unit.clip]).repeat();
            rig.playing = Some(unit.clip);
        }
    }

    let mut shared = bridge.state.lock().unwrap();
    if let Some(view) = view {
        shared.available.push(view.bytes);
        shared.status.tick = battle.tick;
    }
    if options.inspect {
        let bones = transforms.p2();
        let pose = battle
            .inspected_joints
            .map(|joint| joint.and_then(|entity| bones.get(entity).ok()).copied());
        if let [Some(head), Some(thigh), Some(recoil)] = pose {
            let current = [head, thigh, recoil];
            if shared.status.clip == active_clip
                && battle.last_pose.is_some_and(|old| {
                    old.iter().zip(current).any(|(previous, next)| {
                        previous.translation.distance_squared(next.translation) > 1e-10
                            || previous.rotation.angle_between(next.rotation).abs() > 0.0001
                            || previous.scale.distance_squared(next.scale) > 1e-10
                    })
                })
            {
                shared.status.pose_changes[active_clip] += 1;
            }
            shared.status.clip = active_clip;
            battle.last_pose = Some(current);
        }
        if exit.0 && shared.status.pose_changes.iter().all(|&count| count >= 8) {
            shared.report = Some(serde_json::to_string(&shared.status).unwrap());
            app_exit.write(AppExit::Success);
        }
        return;
    }

    if measuring && shared.report.is_none() {
        battle.frame_ms.push(time.delta_secs_f64() * 1000.0);
        battle
            .update_ms
            .push(update_start.elapsed().as_secs_f64() * 1000.0);
    }
    if shared.report.is_none()
        && shared
            .simulation
            .as_ref()
            .is_some_and(|sim| battle.tick == sim.trace.ticks)
    {
        let frame = Timing::from_samples(&mut battle.frame_ms);
        let mean_frames_per_second = if frame.mean_ms > 0.0 {
            1000.0 / frame.mean_ms
        } else {
            0.0
        };
        let report = RenderReport {
            options: options.clone(),
            status: shared.status.clone(),
            actual_resolution: [window.physical_width(), window.physical_height()],
            frame,
            mean_frames_per_second,
            render_update: Timing::from_samples(&mut battle.update_ms),
            view_queue: Timing::from_samples(&mut battle.queue_ms),
            views_applied: battle.applied,
            views_replaced: shared.replaced,
            simulation: shared.simulation.take().expect("completed worker"),
        };
        shared.report = Some(serde_json::to_string(&report).unwrap());
        if exit.0 {
            app_exit.write(AppExit::Success);
        }
    }
}
