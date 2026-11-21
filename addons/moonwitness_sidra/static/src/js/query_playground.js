/** @flectra-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@flectra/owl";

export class SidraQueryPlayground extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.state = useState({
            query: "",
            tradition_code: "",
            language: "",
            loading: false,
            result: null,
            error: "",
            feedbackSent: false,
        });
    }

    async onSubmit(ev) {
        ev.preventDefault();
        const q = (this.state.query || "").trim();
        if (!q) {
            this.state.error = "Masukkan kata kunci atau pertanyaan riset terlebih dahulu.";
            return;
        }
        this.state.loading = true;
        this.state.error = "";
        this.state.feedbackSent = false;
        try {
            const res = await this.rpc("/sidra/api/query", {
                query: q,
                tradition_code: this.state.tradition_code || undefined,
                language: this.state.language || undefined,
                session_id: "flectra-ui-playground",
                limit: 8,
            });
            if (!res.ok) {
                this.state.error = (res.error && res.error.message) || "Query gagal dijalankan.";
                this.state.result = null;
            } else {
                this.state.result = res;
            }
        } catch (err) {
            this.state.error = String(err.message || err);
        } finally {
            this.state.loading = false;
        }
    }

    async sendFeedback(feedback) {
        if (!this.state.result || !this.state.result.query_log_id) return;
        try {
            await this.rpc("/sidra/api/feedback", {
                query_log_id: this.state.result.query_log_id,
                feedback,
            });
            this.state.feedbackSent = true;
            this.notification.add(`Audit feedback '${feedback}' tercatat di Query Log.`, { type: "success" });
        } catch (err) {
            this.notification.add(String(err.message || err), { type: "danger" });
        }
    }
}

SidraQueryPlayground.template = "moonwitness_sidra.QueryPlayground";

registry.category("actions").add("moonwitness_sidra.query_playground", SidraQueryPlayground);
