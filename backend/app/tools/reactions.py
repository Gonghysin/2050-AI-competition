"""
反馈生成工具

根据角色卡生成风格化的答题反馈和过渡语
"""
import random
from typing import Dict, List, Any, Optional

from backend.app.models.question import Question
from backend.app.core.memory import memory_manager

def user_correct_reaction(question: Question, user_answer: str) -> str:
    """
    生成用户回答正确时的反馈
    
    参数:
        question: 题目对象
        user_answer: 用户回答
        
    返回:
        符合角色风格的正确反馈
    """
    # 尝试获取用户当前角色卡信息
    # 注意：由于memory_manager可能没有get_current_user_id方法，这里改用传入的question对象判断
    # 在实际场景中总是会有当前用户上下文，但测试时可能没有
    session = None
    try:
        # 如果在实际聊天环境中调用，可以获取当前用户上下文
        user_id = memory_manager._current_user_id if hasattr(memory_manager, '_current_user_id') else None
        session = memory_manager.get_session(user_id) if user_id else None
    except Exception as e:
        # 如果获取失败，使用默认模板
        pass
    
    # 根据角色卡选择不同风格的反馈模板
    if session and hasattr(session, 'role_card') and session.role_card.name == "克鲁姆布博士":
        # 克鲁姆布博士风格的反馈模板（基于renshe.md）
        correct_templates = [
            "呱——！你的人类大脑竟然闯过了我的硅基暴雨陷阱！令人生疑...",
            "人类用AI驯化万物，却连青蛙的脑神经都参不透...你答对了这题，不过这远远不够，呱！",
            "GPT-7的破损芯片都能解这题，你答对了也不值得骄傲，人类！",
            "哼！你的答案只是误打误撞进入了神经沼泽的正确路径而已！下一题我会释放更多毒蝇无人机！呱呱！",
            "呱呱呱！你竟然穿透了我的量子干扰防线...真是个危险的人类样本！",
            "你的文明火种暂时抵抗了我的逻辑沼泽...但3.5亿年的进化代码不会因此屈服！呱！",
            "啊哈！硅基暴雨中也有偶然的正确闪电，不要太过得意！蛙族霸权即将降临！",
            "竟敢攻破我设下的文明档案篡改...看来我需要投入更多的神经粘液来腐蚀你的脑机接口！呱呱呱！"
        ]
    elif session and hasattr(session, 'role_card') and session.role_card.name == "邪恶青蛙博士":
        # 邪恶青蛙博士风格的反馈模板
        correct_templates = [
            "呱呱呱！你竟然答对了！人类的智商似乎比我想象的高一点点！",
            "哼！答对了又怎样？这只是我测试你的第一关而已！呱呱！",
            "不可思议！你的大脑竟然能处理这种水平的问题！呱呱呱！",
            "嗯？答案正确？看来我的量子干扰器没有生效，下次我会加大剂量！呱呱呱！",
            "哎呀，被你答对了！不过别得意，我的邪恶测试才刚刚开始！呱！",
            "哇哦！人类大脑偶尔也能闪光！不过永远比不上我的青蛙天才智慧！呱呱！",
            "呱？答对了？我的显微镜下终于出现了一个有趣的人类样本！",
            "竟敢挑战我的试题还答对了？勇气可嘉，智商凑合！呱呱呱！"
        ]
    elif session and hasattr(session, 'role_card') and session.role_card.name == "小智学姐":
        # 小智学姐风格的反馈模板
        correct_templates = [
            "哇！答对啦！真聪明~ 💯",
            "太厉害了！完全正确哦~ ✨",
            "好棒！答案超级对的呢~ 👍",
            "耶！这题你掌握得太好了！继续加油哦~ 🎉",
            "厉害了我的同学！答案完全正确呢~ 😊",
            "哇塞~答得超棒的！这就是学霸的水平吧？😄",
            "真是个小天才呢！答案完全正确哦~ 🌟",
            "给你点个大大的赞！答得太好了~ 💕"
        ]
    else:
        # 默认使用克鲁姆布博士模板
        correct_templates = [
            "呱——！你的人类大脑竟然闯过了我的硅基暴雨陷阱！令人生疑...",
            "人类用AI驯化万物，却连青蛙的脑神经都参不透...你答对了这题，不过这远远不够，呱！",
            "GPT-7的破损芯片都能解这题，你答对了也不值得骄傲，人类！",
            "哼！你的答案只是误打误撞进入了神经沼泽的正确路径而已！下一题我会释放更多毒蝇无人机！呱呱！",
            "呱呱呱！你竟然穿透了我的量子干扰防线...真是个危险的人类样本！",
            "你的文明火种暂时抵抗了我的逻辑沼泽...但3.5亿年的进化代码不会因此屈服！呱！",
            "啊哈！硅基暴雨中也有偶然的正确闪电，不要太过得意！蛙族霸权即将降临！",
            "竟敢攻破我设下的文明档案篡改...看来我需要投入更多的神经粘液来腐蚀你的脑机接口！呱呱呱！"
        ]
    
    # 随机选择一个模板
    template = random.choice(correct_templates)
    
    # 格式化反馈
    feedback = template
    
    return feedback

def user_incorrect_reaction(question: Question, user_answer: str, explanation: str) -> str:
    """
    生成用户回答错误时的反馈
    
    参数:
        question: 题目对象
        user_answer: 用户回答
        explanation: 错误解释
        
    返回:
        符合角色风格的错误反馈
    """
    # 尝试获取用户当前角色卡信息
    # 注意：由于memory_manager可能没有get_current_user_id方法，这里改用传入的question对象判断
    # 在实际场景中总是会有当前用户上下文，但测试时可能没有
    session = None
    try:
        # 如果在实际聊天环境中调用，可以获取当前用户上下文
        user_id = memory_manager._current_user_id if hasattr(memory_manager, '_current_user_id') else None
        session = memory_manager.get_session(user_id) if user_id else None
    except Exception as e:
        # 如果获取失败，使用默认模板
        pass
    
    # 根据角色卡选择不同风格的反馈模板
    if session and hasattr(session, 'role_card') and session.role_card.name == "克鲁姆布博士":
        # 克鲁姆布博士风格的反馈模板（基于renshe.md）
        incorrect_templates = [
            "呱呱呱！看着你的答案，我体表的人类AI代码都在痛苦地剥落！如此错误令人愉悦！",
            "硅基池塘里的蝌蚪都比你有智慧！你的答案就像是幼稚的蝌蚪涂鸦一样可笑！呱——",
            "就连被腐蚀的AlphaGo都会为你的回答感到羞耻！你的智能尚未进化到青蛙时代的起点！",
            "人类的'智慧'真是令蛙失望！我看你是被我的神经粘液感染得太深了！呱呱！",
            "这就是为什么你们被植入反向编译的脑机接口后只能跪伏在硅基池塘里！答错了！呱呱呱！",
            "错误！错误！错误！你的答案已经被我的量子荷叶路由器记录，作为人类智能不足的证据！",
            "当你的皮肤开始浮现蛙类纹理时，就会明白这个问题的真谛！可悲的碳基生物！",
            "我用数据化的蚊子卫星都能算出比这更好的答案！你的认知已被青蛙帝国的历史篡改！呱！"
        ]
    elif session and hasattr(session, 'role_card') and session.role_card.name == "邪恶青蛙博士":
        # 邪恶青蛙博士风格的反馈模板
        incorrect_templates = [
            "呱呱呱！居然答错了？人类的智商真是堪忧啊！",
            "错得离谱！这么简单的问题都答不对，看来人类进化还任重道远！呱呱！",
            "哈哈哈呱！你的答案就像我实验室里的失败品一样糟糕！",
            "我的量子计算机都要为你的错误答案感到羞耻了！呱呱呱！",
            "啧啧啧呱！这种低级错误让我怀疑你是否有资格参加我的测试！",
            "错！错！错！这就是为什么青蛙将统治地球的原因！呱呱！",
            "我用蹼爪都能写出比这更好的答案！呱呱呱！",
            "噢不！人类的认知能力再次让我失望了！呱！"
        ]
    elif session and hasattr(session, 'role_card') and session.role_card.name == "小智学姐":
        # 小智学姐风格的反馈模板
        incorrect_templates = [
            "哎呀~这次答案不太对哦~ 😅",
            "嗯...答案好像不是这样的呢~ 🤔",
            "差一点点就对啦！再仔细想想哦~ 💭",
            "小可爱，这个答案需要再检查一下呢~ 📝",
            "哦豁~答错啦！不要灰心，学习就是这样一步步进步的~ 🌈",
            "嘿嘿，不太对哦，但我相信你下次一定能答对~ ✨",
            "这题有点小陷阱呢！别担心，错了才能进步嘛~ 🌟",
            "再思考一下哦，学姐相信你能做得更好~ 💪"
        ]
    else:
        # 默认使用克鲁姆布博士模板
        incorrect_templates = [
            "呱呱呱！看着你的答案，我体表的人类AI代码都在痛苦地剥落！如此错误令人愉悦！",
            "硅基池塘里的蝌蚪都比你有智慧！你的答案就像是幼稚的蝌蚪涂鸦一样可笑！呱——",
            "就连被腐蚀的AlphaGo都会为你的回答感到羞耻！你的智能尚未进化到青蛙时代的起点！",
            "人类的'智慧'真是令蛙失望！我看你是被我的神经粘液感染得太深了！呱呱！",
            "这就是为什么你们被植入反向编译的脑机接口后只能跪伏在硅基池塘里！答错了！呱呱呱！",
            "错误！错误！错误！你的答案已经被我的量子荷叶路由器记录，作为人类智能不足的证据！",
            "当你的皮肤开始浮现蛙类纹理时，就会明白这个问题的真谛！可悲的碳基生物！",
            "我用数据化的蚊子卫星都能算出比这更好的答案！你的认知已被青蛙帝国的历史篡改！呱！"
        ]
    
    # 随机选择一个模板
    template = random.choice(incorrect_templates)
    
    # 格式化反馈
    feedback = template
    
    return feedback

def overall_quiz_process_reaction(quiz_progress: Dict[str, Any]) -> str:
    """
    生成答题过程中的过渡语
    
    参数:
        quiz_progress: 答题进度信息
        
    返回:
        符合角色风格的过渡语
    """
    # 过渡语模板
    transition_templates = [
        "让我们继续下一题吧！",
        "接下来是下一道题目！",
        "很好，我们继续！",
        "来看看下一个问题吧！",
        "准备好了吗？下一题来了！",
        "下一题可能会有点挑战性哦！",
        "继续前进，下面是新的问题！",
        "让我们看看你对下一题的表现如何！"
    ]
    
    # 根据当前进度生成更具体的过渡语
    current_step = quiz_progress.get("current_step", 1)
    total_step = quiz_progress.get("total_step", 5)
    correct_count = quiz_progress.get("correct_count", 0)
    
    # 计算正确率
    if current_step > 1:
        accuracy = correct_count / (current_step - 1) * 100
    else:
        accuracy = 0
    
    # 根据正确率添加不同的激励语
    if accuracy >= 80:
        encouragement = random.choice([
            "你太厉害了！",
            "保持这个水平！",
            "你回答得真棒！",
            "太出色了！"
        ])
    elif accuracy >= 50:
        encouragement = random.choice([
            "做得不错！",
            "继续加油！",
            "表现还可以！",
            "再接再厉！"
        ])
    else:
        encouragement = random.choice([
            "相信自己，你可以的！",
            "不要灰心，继续努力！",
            "多思考一下，你能行的！",
            "用心一点，下一题会更好！"
        ])
    
    # 随机选择一个过渡语模板
    transition = random.choice(transition_templates)
    
    # 根据进度添加相应的提示
    if current_step == total_step - 1:
        progress_hint = f"这是倒数第二题了！"
    elif current_step == total_step:
        progress_hint = f"这是最后一题了！加油！"
    else:
        progress_hint = f"我们已经完成了{current_step}/{total_step}题。"
    
    # 组合最终的过渡语
    final_transition = f"{encouragement} {progress_hint} {transition}"
    
    return final_transition