import sys
sys.path.append('../')

from .Dataset import Dataset

import torch
import torch.utils.data.distributed
import logging
import os
import numpy as np

class CIFAR100QAggAdv(Dataset):

    def __init__(self, size, args):
        super().__init__(size, args)

        self.trainset = None
        self.proxyset = None
        self.valset = None
        self.testset = None
        self.args = args
        self.rng = np.random.default_rng(args.seed)
        self.generator = torch.Generator().manual_seed(args.seed)
        
        if not self.args.proxy_set:
            raise ValueError('Proxy set must be specified for CIFARQ100AggAdv')
        if not self.args.logitpath:
            raise ValueError('Logit path must be specified for CIFARQ100AggAdv')

        self.generator = torch.Generator().manual_seed(self.args.seed)
        self.num_classes = 100
        self.load_trainset()
        self.load_testset()

    def load_trainset(self):
        logging.info('==> load train data')
        
        logit_trainset_path = os.path.join(self.args.logitpath, 'logit_trainset.pth')
        self.logit_trainset = torch.load(logit_trainset_path)
        for i in range(len(self.logit_trainset)):
            self.logit_trainset[i] = [((x1, x2), y) for x1, x2, y in self.logit_trainset[i]]
        self.num_samples = np.array([len(self.logit_trainset[i]) for i in range(len(self.logit_trainset))])
    
    def load_testset(self):
        logging.info('==> load test data')

        logit_testset_path = os.path.join(self.args.logitpath, 'logit_testset.pth')
        self.logit_testset = torch.load(logit_testset_path)
        self.logit_testset = [((x1, x2), y) for x1, x2, y in self.logit_testset]
        self.logit_valset = None
        
        logging.info('==> val set size: {}'.format(len(self.logit_valset) if self.logit_valset else 0))
        logging.info('==> test set size: {}'.format(len(self.logit_testset)))

    def fetch(self, client_index):

        train_loader = torch.utils.data.DataLoader(self.logit_trainset[client_index], 
                    batch_size=self.args.bs, 
                    shuffle=True, 
                    pin_memory=True)
            
        logging.info('==> Client id {}, samples from trainset {}, samples from proxyset: {}' \
            .format(client_index, len(self.logit_trainset[client_index]), 0))
    
        test_loader = torch.utils.data.DataLoader(self.logit_testset, 
                                            batch_size=self.args.test_bs, 
                                            shuffle=False, 
                                            num_workers=1)
        
        # TODO: if required, not saving valset in logit files currently
        val_loader = None
        # TODO: if required; not saving local testset in logit files currently
        local_test_loader = None
        return train_loader, None, val_loader, test_loader, local_test_loader, self.num_samples

