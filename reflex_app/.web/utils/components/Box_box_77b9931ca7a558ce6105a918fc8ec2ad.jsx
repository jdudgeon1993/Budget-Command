
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_77b9931ca7a558ce6105a918fc8ec2ad = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_3b4e91f2fd2e6730b58f925afe7fc40e = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.save_wi_scenario", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["padding"] : "9px", ["borderRadius"] : "7px", ["cursor"] : "pointer", ["fontSize"] : "12px", ["fontWeight"] : "600", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["textAlign"] : "center", ["background"] : "#BF5AF218", ["color"] : "#BF5AF2", ["border"] : "1px solid #BF5AF244", ["&:hover"] : ({ ["background"] : "#BF5AF228" }), ["&:active"] : ({ ["transform"] : "scale(0.98)" }) }),onClick:on_click_3b4e91f2fd2e6730b58f925afe7fc40e,role:"button",tabIndex:0},children)
    )
});
