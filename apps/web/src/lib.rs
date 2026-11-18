#[cfg(target_arch = "wasm32")]
mod web {
    use js_sys::Uint8Array;
    use std::cell::RefCell;
    use tc_client::{Bridge, Options};
    use wasm_bindgen::prelude::*;

    thread_local! {
        static BRIDGE: RefCell<Option<Bridge>> = const { RefCell::new(None) };
    }

    #[wasm_bindgen]
    pub fn start(options: &str) -> Result<(), JsValue> {
        let options: Options = serde_json::from_str(options).map_err(js_error)?;
        options.validate().map_err(js_error)?;
        let bridge = Bridge::new(options.units);
        BRIDGE.set(Some(bridge.clone()));
        tc_client::run(options, bridge, "assets".to_owned(), false);
        Ok(())
    }

    #[wasm_bindgen]
    pub fn push_view(tick: u32, bytes: Uint8Array) -> Result<bool, JsValue> {
        with_bridge(|bridge| {
            if bytes.length() as usize != bridge.view_len() {
                return Err(JsValue::from_str("invalid worker snapshot length"));
            }
            Ok(bridge.publish(tick, |dest| bytes.copy_to(dest)))
        })
    }

    #[wasm_bindgen]
    pub fn finish(summary: &str) -> Result<(), JsValue> {
        let report = serde_json::from_str(summary).map_err(js_error)?;
        with_bridge(|bridge| bridge.finish(report));
        Ok(())
    }

    #[wasm_bindgen]
    pub fn status() -> String {
        with_bridge(|bridge| serde_json::to_string(&bridge.status()).unwrap())
    }

    #[wasm_bindgen]
    pub fn report() -> Option<String> {
        with_bridge(Bridge::report)
    }

    #[wasm_bindgen]
    pub fn select_clip(index: i32) {
        with_bridge(|bridge| bridge.select_clip(usize::try_from(index).ok().filter(|&i| i < 3)));
    }

    fn with_bridge<T>(f: impl FnOnce(&Bridge) -> T) -> T {
        BRIDGE.with_borrow(|bridge| f(bridge.as_ref().expect("renderer started")))
    }

    fn js_error(error: impl std::fmt::Display) -> JsValue {
        JsValue::from_str(&error.to_string())
    }
}
