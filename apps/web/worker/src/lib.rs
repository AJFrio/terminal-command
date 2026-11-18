#[cfg(target_arch = "wasm32")]
mod worker {
    use tc_session::Replay;
    use wasm_bindgen::prelude::*;

    #[wasm_bindgen]
    pub struct Simulation {
        replay: Option<Replay>,
        view: Vec<u8>,
    }

    #[wasm_bindgen]
    impl Simulation {
        #[wasm_bindgen(constructor)]
        pub fn new(units: usize, seed: u32) -> Result<Simulation, JsValue> {
            let replay = Replay::new(units, seed).map_err(JsValue::from_str)?;
            Ok(Self {
                view: vec![0; replay.view_len()],
                replay: Some(replay),
            })
        }

        pub fn step(&mut self) {
            self.replay.as_mut().expect("active simulation").step();
        }

        pub fn record(&mut self, final_tick: bool) {
            self.replay
                .as_mut()
                .expect("active simulation")
                .record(final_tick);
        }

        pub fn write_view(&mut self) -> *const u8 {
            self.replay
                .as_ref()
                .expect("active simulation")
                .write_view(&mut self.view);
            self.view.as_ptr()
        }

        pub fn view_len(&self) -> usize {
            self.view.len()
        }

        pub fn finish(&mut self) -> String {
            let trace = self.replay.take().expect("active simulation").finish();
            serde_json::to_string(&trace).expect("serializable trace")
        }
    }
}
