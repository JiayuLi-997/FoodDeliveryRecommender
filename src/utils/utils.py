# -*- coding: UTF-8 -*-

import os
import random
import logging
import torch
import datetime
import numpy as np
import pandas as pd
from typing import List, Dict, NoReturn, Any
from torch import nn

def init_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def df_to_dict(df: pd.DataFrame) -> dict:
    res = df.to_dict('list')
    for key in res:
        res[key] = np.array(res[key])
    return res


def batch_to_gpu(batch: dict, device) -> dict:
    for c in batch:
        if type(batch[c]) is torch.Tensor:
            batch[c] = batch[c].to(device)
    return batch


def check(check_list: List[tuple]) -> NoReturn:
    # observe selected tensors during training.
    logging.info('')
    for i, t in enumerate(check_list):
        d = np.array(t[1].detach().cpu())
        logging.info(os.linesep.join(
            [t[0] + '\t' + str(d.shape), np.array2string(d, threshold=20)]
        ) + os.linesep)


def eval_list_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]) and (col[-2:]=='_s' or col=='neg_items'):
            df[col] = df[col].apply(lambda x: eval(str(x)))  # some list-value columns
    return df


def format_metric(result_dict: Dict[str, Any]) -> str:
    assert type(result_dict) == dict
    format_str = []
    metrics = np.unique([k.split('@')[0] for k in result_dict.keys()])
    topks = np.unique([int(k.split('@')[1]) for k in result_dict.keys() if '@' in k])
    if len(topks):
        for topk in np.sort(topks):
            for metric in np.sort(metrics):
                name = '{}@{}'.format(metric, topk)
                m = result_dict[name]
                if type(m) is float or type(m) is np.float or type(m) is np.float32 or type(m) is np.float64:
                    format_str.append('{}:{:<.4f}'.format(name, m))
                elif type(m) is int or type(m) is np.int or type(m) is np.int32 or type(m) is np.int64:
                    format_str.append('{}:{}'.format(name, m))
    else:
        for metric in np.sort(metrics):
            name = metric 
            m = result_dict[name]
            if type(m) is float or type(m) is np.float or type(m) is np.float32 or type(m) is np.float64:
                format_str.append('{}:{:<.4f}'.format(name, m))
            elif type(m) is int or type(m) is np.int or type(m) is np.int32 or type(m) is np.int64:
                format_str.append('{}:{}'.format(name, m))
        
    return ','.join(format_str)


def format_arg_str(args, exclude_lst: list, max_len=20) -> str:
    linesep = os.linesep
    arg_dict = vars(args)
    keys = [k for k in arg_dict.keys() if k not in exclude_lst]
    values = [arg_dict[k] for k in keys]
    key_title, value_title = 'Arguments', 'Values'
    key_max_len = max(map(lambda x: len(str(x)), keys))
    value_max_len = min(max(map(lambda x: len(str(x)), values)), max_len)
    key_max_len, value_max_len = max([len(key_title), key_max_len]), max([len(value_title), value_max_len])
    horizon_len = key_max_len + value_max_len + 5
    res_str = linesep + '=' * horizon_len + linesep
    res_str += ' ' + key_title + ' ' * (key_max_len - len(key_title)) + ' | ' \
               + value_title + ' ' * (value_max_len - len(value_title)) + ' ' + linesep + '=' * horizon_len + linesep
    for key in sorted(keys):
        value = arg_dict[key]
        if value is not None:
            key, value = str(key), str(value).replace('\t', '\\t')
            value = value[:max_len-3] + '...' if len(value) > max_len else value
            res_str += ' ' + key + ' ' * (key_max_len - len(key)) + ' | ' \
                       + value + ' ' * (value_max_len - len(value)) + linesep
    res_str += '=' * horizon_len
    return res_str


def check_dir(file_name: str) -> NoReturn:
    dir_path = os.path.dirname(file_name)
    if not os.path.exists(dir_path):
        print('make dirs:', dir_path)
        os.makedirs(dir_path)


def non_increasing(lst: list) -> bool:
    return all(x >= y for x, y in zip([lst[0]]*(len(lst)-1), lst[1:])) # update the calculation of non_increasing to fit ealry stopping, 2023.5.14, Jiayu Li


def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_activation(activation, hidden_units=None):
    if isinstance(activation, str):
        if activation.lower() in ["prelu", "dice"]:
            assert type(hidden_units) == int
        if activation.lower() == "relu":
            return nn.ReLU()
        elif activation.lower() == "sigmoid":
            return nn.Sigmoid()
        elif activation.lower() == "tanh":
            return nn.Tanh()
        elif activation.lower() == "softmax":
            return nn.Softmax(dim=-1)
        elif activation.lower() == "prelu":
            return nn.PReLU(hidden_units, init=0.1)
        # elif activation.lower() == "dice":
        #     from fuxictr.pytorch.layers.activations import Dice
        #     return Dice(hidden_units)
        else:
            return getattr(nn, activation)()
    elif isinstance(activation, list):
        if hidden_units is not None:
            assert len(activation) == len(hidden_units)
            return [get_activation(act, units) for act, units in zip(activation, hidden_units)]
        else:
            return [get_activation(act) for act in activation]
    return activation
