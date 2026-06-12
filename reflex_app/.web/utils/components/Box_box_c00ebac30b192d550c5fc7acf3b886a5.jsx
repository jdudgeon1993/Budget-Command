
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_c00ebac30b192d550c5fc7acf3b886a5 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_c1b59a307c088b31099201cd19969200 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.close_edit_paycheck", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 16px", ["borderRadius"] : "8px", ["border"] : "1px solid rgba(255,255,255,0.08)", ["color"] : "#9090B8", ["fontSize"] : "12px", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["&:hover"] : ({ ["background"] : "rgba(255,255,255,0.08)" }) }),onClick:on_click_c1b59a307c088b31099201cd19969200},children)
    )
});
