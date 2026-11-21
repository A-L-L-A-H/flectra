/** @flectra-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onWillUnmount } from "@flectra/owl";

const PAIRING_POLL_MS = 3000;
const CONNECTED_POLL_MS = 10000;

export class WhatsAppDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.state = useState({
            status: null,
            qr: null,
            error: "",
            sending: false,
            logging_out: false,
            to: "",
            message: "",
        });
        this.unmounted = false;
        onWillStart(() => this.refresh());
        onWillUnmount(() => {
            this.unmounted = true;
            clearTimeout(this.timer);
        });
    }

    async refresh() {
        if (this.refreshing) return;
        this.refreshing = true;
        try {
            const status = await this.rpc("/moonwitness_orchestrator/wa_status", {});
            this.state.status = status.status;
            if (status.pairing_required && status.qr_available) {
                const qr = await this.rpc("/moonwitness_orchestrator/wa_qr", {});
                const nextQr = qr.qr || null;
                if (this.state.qr !== nextQr) {
                    this.state.qr = nextQr;
                }
            } else {
                this.state.qr = null;
            }
            this.state.error = "";
        } catch (err) {
            this.state.error = String(err.message || err);
        } finally {
            this.refreshing = false;
            if (!this.state.logging_out && !this.unmounted) {
                const connected = this.state.status === "connected";
                this.timer = setTimeout(
                    () => this.refresh(),
                    connected ? CONNECTED_POLL_MS : PAIRING_POLL_MS,
                );
            }
        }
    }

    async send() {
        if (!this.state.to || !this.state.message || this.state.sending) return;
        this.state.sending = true;
        try {
            await this.rpc("/moonwitness_orchestrator/wa_send", {
                to: this.state.to,
                message: this.state.message,
            });
            this.notification.add("Pesan terkirim", { type: "success" });
            this.state.message = "";
        } catch (err) {
            this.notification.add(String(err.message || err), { type: "danger" });
        } finally {
            this.state.sending = false;
        }
    }

    async logout() {
        if (this.state.logging_out) return;
        this.state.logging_out = true;
        clearTimeout(this.timer);
        try {
            await this.rpc("/moonwitness_orchestrator/wa_logout", {});
            this.state.qr = null;
        } catch (err) {
            this.notification.add(String(err.message || err), { type: "danger" });
        } finally {
            this.state.logging_out = false;
            this.refresh();
        }
    }
}

WhatsAppDashboard.template = "moonwitness_orchestrator.WhatsAppDashboard";

registry.category("actions").add("moonwitness_orchestrator.whatsapp", WhatsAppDashboard);
