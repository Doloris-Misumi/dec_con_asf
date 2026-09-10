from .detector3d_template import Detector3DTemplate


class PointPillarTaskDec(Detector3DTemplate):
    def __init__(self, model_cfg, num_class, dataset):
        super().__init__(model_cfg=model_cfg, num_class=num_class, dataset=dataset)
        self.module_list = self.build_networks()

    def forward(self, batch_dict):
        for cur_module in self.module_list:
            batch_dict = cur_module(batch_dict)

        if self.training:
            loss, tb_dict, disp_dict = self.get_training_loss(batch_dict)
            if 'cen_loss' in batch_dict:
                loss = loss + batch_dict['cen_loss']
            return {'loss': loss}, tb_dict, disp_dict

        pred_dicts, recall_dicts = self.post_processing(batch_dict)
        if len(pred_dicts) > 0:
            pred_dicts[0]['batch_dict'] = batch_dict
        return pred_dicts, recall_dicts

    def get_training_loss(self, batch_dict):
        disp_dict = {}
        loss_rpn, tb_dict = self.dense_head.get_loss()
        loss = loss_rpn

        patch_dec_loss = batch_dict.get('patch_dec_loss', None)
        if patch_dec_loss is not None:
            patch_dec_weight = float(self.model_cfg.get('PATCH_DEC_WEIGHT', 1.0))
            loss = loss + patch_dec_weight * patch_dec_loss
            tb_dict['loss_patch_dec'] = patch_dec_loss.item()
            tb_dict['loss_patch_dec_weighted'] = (patch_dec_weight * patch_dec_loss).item()

        patch_dec_logging = batch_dict.get('patch_dec_logging', None)
        if patch_dec_logging is not None:
            tb_dict.update(patch_dec_logging)

        tb_dict = {
            'loss_rpn': loss_rpn.item(),
            **tb_dict
        }
        return loss, tb_dict, disp_dict
