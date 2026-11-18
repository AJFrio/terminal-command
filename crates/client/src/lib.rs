mod bridge;
mod scene;

use bevy::{
    asset::{AssetMetaCheck, AssetPlugin},
    prelude::*,
    render::renderer::RenderAdapterInfo,
    window::{MonitorSelection, PresentMode, WindowMode, WindowResolution},
};
pub use bridge::{Bridge, Options, RenderReport, Status};

pub fn run(
    options: Options,
    bridge: Bridge,
    asset_root: String,
    exit_after_report: bool,
) -> AppExit {
    let description = if options.inspect {
        "Rivet inspection · 1 Idle / 2 Move / 3 Fire / 4 Cycle".to_owned()
    } else {
        format!("{} units · {} Rivet rigs", options.units, options.rigs)
    };
    let mut app = App::new();
    app.insert_resource(ClearColor(Color::srgb(0.10, 0.13, 0.15)))
        .insert_resource(GlobalAmbientLight {
            color: Color::srgb(0.82, 0.9, 1.0),
            brightness: 560.0,
            ..default()
        })
        .add_plugins(
            DefaultPlugins
                .set(AssetPlugin {
                    file_path: asset_root,
                    meta_check: AssetMetaCheck::Never,
                    ..default()
                })
                .set(WindowPlugin {
                    primary_window: Some(Window {
                        title: format!("Terminal Command  /  {description}"),
                        resolution: WindowResolution::new(options.width, options.height)
                            .with_scale_factor_override(1.0),
                        mode: if options.fullscreen {
                            WindowMode::BorderlessFullscreen(MonitorSelection::Current)
                        } else {
                            WindowMode::Windowed
                        },
                        canvas: cfg!(target_arch = "wasm32").then(|| "#battlefield".into()),
                        present_mode: PresentMode::AutoNoVsync,
                        resizable: false,
                        ..default()
                    }),
                    ..default()
                }),
        )
        .insert_resource(options)
        .insert_resource(bridge)
        .insert_resource(scene::ExitAfterReport(exit_after_report))
        .init_resource::<scene::Battle>()
        .add_systems(Startup, (scene::setup, renderer_info))
        .add_systems(Update, (scene::prepare_rigs, scene::update).chain());
    app.run()
}

fn renderer_info(bridge: Res<Bridge>, device: Option<Res<RenderAdapterInfo>>) {
    if let Some(device) = device {
        let mut shared = bridge.state.lock().unwrap();
        shared.status.adapter = device.name.clone();
        shared.status.backend = format!("{:?}", device.backend);
    }
}
