/* Registered once as a dashboard resource. Always loads the current implementation
 * (no browser cache); the implementation in turn loads the 3D module. */
import("/local/floorplan/v4/floorplan-v4-impl.js?t=" + Date.now());
import("/local/floorplan/v4/alert-popup.js?t=" + Date.now()).catch((e) => console.error("alert-popup failed", e));
