/** @flectra-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onWillUnmount } from "@flectra/owl";

const POLL_MS = 3000;

export class WhatsAppDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.state = useState({
            status: null,
            qr: null,
            error: "",
            sending: false,
            to: "",
            message: "",
        });
        onWillStart(() => this.refresh(true));
        this.timer = setInterval(() => this.refresh(false), POLL_MS);
        onWillUnmount(() => clearInterval(this.timer));
    }

    async refresh(withQr) {
        try {
            const status = await this.rpc("/moonwitness_orchestrator/wa_status", {});
            this.state.status = status.status;
            if (withQr && status.pairing_required) {
                const qr = await this.rpc("/moonwitness_orchestrator/wa_qr", {});
                this.state.qr = qr.qr || null;
            }
            this.state.error = "";
        } catch (err) {
            this.state.error = String(err.message || err);
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
        await this.rpc("/moonwitness_orchestrator/wa_logout", {});
        this.state.qr = null;
        this.refresh(true);
    }
}

WhatsAppDashboard.template = "moonwitness_orchestrator.WhatsAppDashboard";

registry.category("actions").add("moonwitness_orchestrator.whatsapp", WhatsAppDashboard);
