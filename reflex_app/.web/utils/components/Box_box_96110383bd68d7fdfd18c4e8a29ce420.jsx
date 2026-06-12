
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_96110383bd68d7fdfd18c4e8a29ce420 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_3b4e91f2fd2e6730b58f925afe7fc40e = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.save_wi_scenario", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "6px 14px", ["borderRadius"] : "8px", ["cursor"] : "pointer", ["fontSize"] : "12px", ["background"] : "#818cf818", ["color"] : "#818cf8", ["border"] : "1px solid #818cf844", ["&:hover"] : ({ ["background"] : "#818cf828" }) }),onClick:on_click_3b4e91f2fd2e6730b58f925afe7fc40e},children)
    )
});
