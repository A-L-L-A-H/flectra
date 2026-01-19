/** @flectra-module **/

import { patch } from "@web/core/utils/patch";
import * as spreadsheet from "@flectra/o-spreadsheet";
import { useService } from "@web/core/utils/hooks";
import { navigateToFlectraMenu } from "@spreadsheet/helpers/helpers";

patch(spreadsheet.components.FigureComponent.prototype, {
    setup() {
        super.setup();
        this.menuService = useService("menu");
        this.actionService = useService("action");
        this.notificationService = useService("notification");
    },
    get hasFlectraMenu() {
        return this.env.model.getters.getChartFlectraMenu(this.props.figure.id) !== undefined;
    },
    async onClick() {
        if (this.hasFlectraMenu) {
            await navigateToFlectraMenu({
                figureId: this.props.figure.id,
                model: this.env.model,
                notificationService: this.notificationService,
                actionService: this.actionService,
            });
        }
    },
});
